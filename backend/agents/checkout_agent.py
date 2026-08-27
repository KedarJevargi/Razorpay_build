import logging
import uuid
import asyncpg
from typing import Dict, Any, List
from backend.agents.base_agent import BaseAgent
from backend.agents.exceptions import PaymentVerificationError
from a2a.types import AgentCard
from backend.razorpay.client import RazorpayClient

logger = logging.getLogger(__name__)

class CheckoutAgent(BaseAgent):
    """
    Merchant Specialist: Checkout Agent
    Responsible for managing the cart, initiating checkout via Razorpay, and confirming payments.
    """
    def __init__(self, db_pool: asyncpg.Pool):
        agent_card = AgentCard(
            name="Checkout Agent",
            description=(
                "You are the specialist agent for cart management and payment creation. "
                "CRITICAL: Do NOT ask for a customer_id or user_id. Treat all customers as guests/new customers. "
                "To initiate checkout, you MUST use the user's name, email, phone, and address provided in the intent. "
                "Customer database records are ONLY created upon successful payment."
            )
        )
        super().__init__(agent_card=agent_card)
        self.db_pool = db_pool
        self.rzp_client = RazorpayClient()
        
        self.register_tool(self.add_to_cart)
        self.register_tool(self.view_cart)
        self.register_tool(self.clear_cart)
        self.register_tool(self.remove_from_cart)
        self.register_tool(self.initiate_checkout)
        self.register_tool(self.complete_payment)

    async def _get_or_create_cart(self, conn, session_id: str) -> str:
        """Helper to get active cart or create one."""
        cart = await conn.fetchrow(
            "SELECT id FROM carts WHERE session_id = $1 AND status = 'active'",
            session_id
        )
        if cart:
            return cart["id"]
            
        cart_id = f"cart_{uuid.uuid4().hex[:8]}"
        await conn.execute(
            "INSERT INTO carts (id, session_id, customer_id) VALUES ($1, $2, NULL)",
            cart_id, session_id
        )
        return cart_id

    async def add_to_cart(self, session_id: str, product_identifier: str, quantity: int) -> Dict[str, Any]:
        """Add an item to the active cart for the given session. Resolves product by ID or Name."""
        try:
            quantity = int(quantity)
        except ValueError:
            return {"error": "Quantity must be a valid integer."}
        async with self.db_pool.acquire() as conn:
            # Check inventory & price by ID or Name
            # Match by exact ID, or name contains identifier, or identifier contains name (reverse match)
            product = await conn.fetchrow(
                """SELECT p.id, p.price, p.name, i.quantity as stock 
                FROM products p JOIN inventory i ON p.id = i.product_id 
                WHERE p.id = $1 OR p.name ILIKE $2 OR $3 ILIKE '%' || p.name || '%' 
                LIMIT 1""",
                product_identifier, f"%{product_identifier}%", product_identifier
            )
            if not product:
                return {"error": f"Product '{product_identifier}' not found"}
                
            if product["stock"] < quantity:
                return {"error": f"Insufficient stock. Only {product['stock']} available."}
                
            cart_id = await self._get_or_create_cart(conn, session_id)
            
            # Upsert into cart_items
            item_id = f"ci_{uuid.uuid4().hex[:8]}"
            await conn.execute(
                """
                INSERT INTO cart_items (id, cart_id, product_id, quantity, unit_price)
                VALUES ($1, $2, $3, $4, $5)
                """,
                item_id, cart_id, product["id"], quantity, product["price"]
            )
            
            return {"status": "success", "cart_id": cart_id, "added": {"product_id": product["id"], "name": product["name"], "quantity": quantity}}

    async def view_cart(self, session_id: str) -> Dict[str, Any]:
        """View the current contents of the cart and total."""
        async with self.db_pool.acquire() as conn:
            cart = await conn.fetchrow("SELECT id FROM carts WHERE session_id = $1 AND status = 'active'", session_id)
            if not cart:
                return {"status": "empty"}
                
            items = await conn.fetch(
                """
                SELECT ci.product_id, p.name, ci.quantity, ci.unit_price, (ci.quantity * ci.unit_price) as total
                FROM cart_items ci
                JOIN products p ON ci.product_id = p.id
                WHERE ci.cart_id = $1
                """,
                cart["id"]
            )
            
            if not items:
                return {"status": "empty", "cart_id": cart["id"]}
            
            # Convert Decimal values to float to prevent type mismatches downstream
            items_list = []
            for i in items:
                item = dict(i)
                item["unit_price"] = float(item["unit_price"])
                item["total"] = float(item["total"])
                items_list.append(item)
                
            total = sum(item["total"] for item in items_list)
            return {"status": "success", "cart_id": cart["id"], "total": float(total), "items": items_list}

    async def clear_cart(self, session_id: str) -> Dict[str, Any]:
        """Clears all items from the current active cart."""
        async with self.db_pool.acquire() as conn:
            cart = await conn.fetchrow("SELECT id FROM carts WHERE session_id = $1 AND status = 'active'", session_id)
            if not cart:
                return {"status": "success", "message": "Cart is already empty"}
            await conn.execute("DELETE FROM cart_items WHERE cart_id = $1", cart["id"])
            return {"status": "success", "message": "Cart cleared successfully"}

    async def remove_from_cart(self, session_id: str, product_identifier: str) -> Dict[str, Any]:
        """Removes a specific product from the cart."""
        async with self.db_pool.acquire() as conn:
            cart = await conn.fetchrow("SELECT id FROM carts WHERE session_id = $1 AND status = 'active'", session_id)
            if not cart:
                return {"error": "No active cart found"}
            
            product = await conn.fetchrow("SELECT id FROM products WHERE id ILIKE $1", f"%{product_identifier}%")
            if not product:
                return {"error": f"Product not found: {product_identifier}"}
                
            await conn.execute("DELETE FROM cart_items WHERE cart_id = $1 AND product_id = $2", cart["id"], product["id"])
            return {"status": "success", "message": f"Removed {product_identifier} from cart"}

    async def initiate_checkout(self, session_id: str, merchant_id: str, customer_name: str, customer_email: str, customer_phone: str, shipping_address: str, promo_code: str = None) -> Dict[str, Any]:
        """
        Creates an order in the database and generates a Razorpay order.
        Requires full user details before proceeding to the payment page.
        Optionally accepts a promo_code to apply discounts.
        """
        if not customer_name or not customer_email or not customer_phone or not shipping_address:
            return {"error": "Missing user details. You must provide name, email, phone, and address to checkout."}
            
        async with self.db_pool.acquire() as conn:
            cart_data = await self.view_cart(session_id)
            if cart_data.get("status") != "active":
                return {"error": "Cart is empty or inactive"}
                
            total_amount = cart_data["total"]
            cart_id = cart_data["cart_id"]
            
            discount_total = 0.0
            if promo_code:
                # Try exact match first, then case-insensitive partial match as fallback
                promo = await conn.fetchrow(
                    "SELECT type, value, min_order_value, max_discount FROM promotions WHERE id = $1 AND merchant_id = $2 AND active = true",
                    promo_code, merchant_id
                )
                if not promo:
                    # Fallback: case-insensitive partial match (handles 'Welcome10' -> 'promo_welcome10')
                    promo = await conn.fetchrow(
                        "SELECT type, value, min_order_value, max_discount FROM promotions WHERE id ILIKE $1 AND merchant_id = $2 AND active = true",
                        f"%{promo_code}%", merchant_id
                    )
                if not promo:
                    return {"error": f"Invalid or inactive promo code: {promo_code}"}
                
                # Convert Decimal DB values to float to prevent float*Decimal TypeError
                min_order = float(promo["min_order_value"]) if promo["min_order_value"] else None
                promo_value = float(promo["value"])
                max_disc = float(promo["max_discount"]) if promo["max_discount"] else None
                
                if min_order and total_amount < min_order:
                    return {"error": f"Order total must be at least {min_order} to use this promo code."}
                    
                if promo["type"] == "percentage_discount":
                    calculated = total_amount * (promo_value / 100)
                    if max_disc and calculated > max_disc:
                        calculated = max_disc
                    discount_total = calculated
                elif promo["type"] == "flat_discount":
                    discount_total = promo_value
            
            final_total = total_amount - discount_total
            
            # Amount in paise for Razorpay
            amount_in_paise = int(final_total * 100)
            
            # Create DB Order with NULL customer_id (created post-payment)
            order_id = f"ord_{uuid.uuid4().hex[:8]}"
            
            # Create Razorpay Payment Link
            try:
                plink = self.rzp_client.create_payment_link(
                    amount=amount_in_paise,
                    currency="INR",
                    description="Purchase from AdventureHub",
                    customer_details={
                        "name": customer_name,
                        "email": customer_email,
                        "contact": customer_phone
                    },
                    reference_id=order_id
                )
            except Exception as e:
                return {"error": f"Failed to create Razorpay Payment Link: {str(e)}"}
                
            await conn.execute(
                """
                INSERT INTO orders (id, cart_id, customer_id, merchant_id, total, discount_total, final_total, razorpay_order_id, razorpay_payment_link_id, razorpay_payment_link_url, payment_status, order_status)
                VALUES ($1, $2, NULL, $3, $4, $5, $6, $7, $8, $9, 'pending', 'created')
                """,
                order_id, cart_id, merchant_id, total_amount, discount_total, final_total, 
                plink.get("order_id", ""), plink["id"], plink["short_url"]
            )
            
            # Mark cart as converted
            await conn.execute("UPDATE carts SET status = 'converted' WHERE id = $1", cart_id)
            
            return {
                "status": "checkout_initiated",
                "order_id": order_id,
                "total_amount": total_amount,
                "discount_total": discount_total,
                "final_total": final_total,
                "payment_link_id": plink["id"],
                "payment_link_url": plink["short_url"],
                "message": f"[PAYMENT_LINK] {plink['short_url']}"
            }

    async def verify_payment(self, db_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> Dict[str, Any]:
        """
        Verifies the Razorpay payment signature and updates the order status.
        """
        async with self.db_pool.acquire() as conn:
            order = await conn.fetchrow("SELECT razorpay_order_id FROM orders WHERE id = $1", db_order_id)
            if not order:
                return {"error": "Order not found"}
                
            rzp_order_id = order["razorpay_order_id"]
            
            is_valid = self.rzp_client.verify_payment(rzp_order_id, razorpay_payment_id, razorpay_signature)
            
            if is_valid:
                await conn.execute("UPDATE orders SET payment_status = 'captured', order_status = 'confirmed' WHERE id = $1", db_order_id)
                return {"status": "payment_successful", "order_id": db_order_id}
            else:
                await conn.execute("UPDATE orders SET payment_status = 'failed' WHERE id = $1", db_order_id)
                return {"status": "payment_failed", "error": "Invalid signature or payment declined"}

    async def complete_payment(self, order_id: str, payment_details: str, customer_name: str, customer_email: str, customer_phone: str) -> Dict[str, Any]:
        """
        Completes the payment by verifying the Razorpay Payment Link status.
        Creates the customer record in the database only upon successful payment.
        """
        async with self.db_pool.acquire() as conn:
            order = await conn.fetchrow("SELECT razorpay_payment_link_id FROM orders WHERE id = $1", order_id)
            if not order or not order["razorpay_payment_link_id"]:
                return {"error": f"Order '{order_id}' or Payment Link not found"}
            
            plink_id = order["razorpay_payment_link_id"]
        
        status = self.rzp_client.verify_payment_link_status(plink_id)
        
        # Simulate decline if payment_details contains 'decline'
        if "decline" in payment_details.lower():
            status = "failed"
            
        if status != "paid":
            async with self.db_pool.acquire() as conn:
                await conn.execute("UPDATE orders SET payment_status = 'failed' WHERE id = $1", order_id)
            raise PaymentVerificationError(f"DETERMINISTIC_PAYMENT_FAILED: Payment is incomplete or failed. Current status is '{status}'.")
        
        # Payment successful, capture it
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                "UPDATE orders SET payment_status = 'captured', order_status = 'confirmed' WHERE id = $1",
                order_id
            )
        
        result = {"status": "payment_successful", "order_id": order_id}
        
        if result.get("status") == "payment_successful":
            async with self.db_pool.acquire() as conn:
                # Upsert customer
                customer = await conn.fetchrow("SELECT id FROM customers WHERE email = $1", customer_email)
                if not customer:
                    customer_id = f"cust_{uuid.uuid4().hex[:8]}"
                    await conn.execute(
                        "INSERT INTO customers (id, name, email, phone) VALUES ($1, $2, $3, $4)",
                        customer_id, customer_name, customer_email, customer_phone
                    )
                else:
                    customer_id = customer["id"]
                
                # Link customer to order
                await conn.execute("UPDATE orders SET customer_id = $1 WHERE id = $2", customer_id, order_id)
                result["customer_id"] = customer_id
        
        return result
