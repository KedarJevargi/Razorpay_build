import sys
import os
import asyncio
import asyncpg
from dotenv import load_dotenv

# Add the project root to the Python path so we can import backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from backend.agents.recommendation_agent import RecommendationAgent
from backend.agents.checkout_agent import CheckoutAgent

load_dotenv()

async def test_agents():
    print("\n--- Testing Phase 4 Agents ---")
    
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/commerce")
    
    try:
        # Connect to DB
        pool = await asyncpg.create_pool(db_url)
        print("✅ Database connection successful.")
        
        merchant_id = "merch_adventurehub"
        session_id = "test_session_123"
        customer_id = "cust_001"
        
        # 1. Instantiate Recommendation Agent
        rec_agent = RecommendationAgent(db_pool=pool)
        print(f"✅ Recommendation Agent created: {rec_agent.agent_card.name}")
        
        # Test Upsell for Backpack 30L
        print("\n[Recommendation] Testing Upsell for prod_pack30 (30L Backpack)...")
        upsells = await rec_agent.suggest_upsell(merchant_id, "prod_pack30")
        if upsells:
            print(f"   Upsell found: {upsells[0]['name']} at {upsells[0]['price']} INR")
        else:
            print("   No upsell found.")
            
        # Test Cross-sell for Tent
        print("\n[Recommendation] Testing Cross-sell for prod_tent2p (Tent)...")
        cross_sells = await rec_agent.suggest_cross_sell(merchant_id, "prod_tent2p")
        if cross_sells:
            print(f"   Cross-sells found:")
            for cs in cross_sells:
                print(f"     - {cs['name']} ({cs['price']} INR)")
        else:
            print("   No cross-sells found.")


        # 2. Instantiate Checkout Agent
        checkout_agent = CheckoutAgent(db_pool=pool)
        print(f"\n✅ Checkout Agent created: {checkout_agent.agent_card.name}")
        
        # Add to cart
        print("\n[Checkout] Adding Tent to cart...")
        cart_res = await checkout_agent.add_to_cart(session_id, "prod_tent2p", 1)
        print(f"   Cart Response: {cart_res}")
        
        # View cart
        print("\n[Checkout] Viewing cart...")
        view_res = await checkout_agent.view_cart(session_id)
        print(f"   Cart Total: {view_res.get('total')} INR for {len(view_res.get('items', []))} items")
        
        # Initiate Checkout
        print("\n[Checkout] Initiating Checkout...")
        checkout_res = await checkout_agent.initiate_checkout(session_id, merchant_id, customer_id)
        print(f"   Checkout Response: {checkout_res}")
        
        # Verify Payment (mock failure)
        order_id = checkout_res.get("order_id")
        if order_id:
            print(f"\n[Checkout] Simulating Payment Verification (Decline) for {order_id}...")
            verify_res = await checkout_agent.verify_payment(order_id, "pay_decline_123", "fake_sig")
            print(f"   Verification Response: {verify_res}")
            
            print(f"\n[Checkout] Simulating Payment Verification (Success) for {order_id}...")
            verify_res_success = await checkout_agent.verify_payment(order_id, "pay_success_456", "fake_sig")
            print(f"   Verification Response: {verify_res_success}")
        
    except Exception as e:
        print(f"❌ Error during tests: {e}")
    finally:
        if 'pool' in locals():
            await pool.close()

if __name__ == "__main__":
    asyncio.run(test_agents())
