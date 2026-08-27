import logging
import asyncpg
from typing import Dict, Any, List
from backend.agents.base_agent import BaseAgent
from a2a.types import AgentCard

logger = logging.getLogger(__name__)

class CatalogAgent(BaseAgent):
    """
    Merchant Specialist: Catalog Agent
    Responsible for answering queries about products, inventory, and promotions.
    """
    def __init__(self, db_pool: asyncpg.Pool):
        agent_card = AgentCard(
            name="Catalog Agent",
            description="You are the specialist agent for product discovery and search. Use broad search terms (e.g., if a user asks for 'bags', try searching for 'pack' or 'backpack')."
        )
        super().__init__(agent_card=agent_card)
        self.db_pool = db_pool
        
        # Register read-only SQL tools
        self.register_tool(self.search_products)
        self.register_tool(self.check_inventory)
        self.register_tool(self.get_active_promotions)

    async def search_products(self, merchant_id: str, search_query: str, max_price: float = None, sort_by_price: str = None) -> List[Dict[str, Any]]:
        """
        Search for products by name, category, or description for a specific merchant.
        Optionally filter by a maximum price.
        Optionally sort by price using sort_by_price ('asc' or 'desc').
        """
        query = """
            SELECT id, name, description, price, currency, category 
            FROM products 
            WHERE merchant_id = $1 AND (
                name ILIKE $2 OR category ILIKE $2 OR description ILIKE $2 OR
                name ILIKE $3 OR category ILIKE $3 OR description ILIKE $3 OR
                $4 ILIKE '%' || name || '%'
            )
        """
        
        # Expand "bag" -> "pack" so we hit backpacks
        search_query_2 = search_query.lower().replace("bag", "pack") if "bag" in search_query.lower() else search_query
        
        params = [merchant_id, f"%{search_query}%", f"%{search_query_2}%", search_query]
        
        if max_price is not None and str(max_price).strip():
            try:
                from decimal import Decimal, InvalidOperation
                max_price_val = Decimal(str(max_price))
                # Next parameter index depends on how many we have so far
                query += f" AND price <= ${len(params) + 1}"
                params.append(max_price_val)
            except (ValueError, InvalidOperation):
                pass
                
        if sort_by_price and sort_by_price.lower() == 'asc':
            query += " ORDER BY price ASC"
        elif sort_by_price and sort_by_price.lower() == 'desc':
            query += " ORDER BY price DESC"
            
        query += " LIMIT 10"
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(r) for r in rows]

    async def check_inventory(self, product_id: str) -> Dict[str, Any]:
        """
        Check the inventory levels for a specific product.
        """
        query = """
            SELECT quantity, reserved, warehouse 
            FROM inventory 
            WHERE product_id = $1
        """
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(query, product_id)
            if row:
                return dict(row)
            return {"error": "Product not found in inventory"}

    async def get_active_promotions(self, merchant_id: str) -> List[Dict[str, Any]]:
        """
        Get all currently active promotions for a merchant.
        """
        query = """
            SELECT id, type, value, min_order_value, max_discount 
            FROM promotions 
            WHERE merchant_id = $1 AND active = true 
            AND (valid_until IS NULL OR valid_until > CURRENT_TIMESTAMP)
            AND (valid_from IS NULL OR valid_from <= CURRENT_TIMESTAMP)
        """
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, merchant_id)
            return [dict(r) for r in rows]
