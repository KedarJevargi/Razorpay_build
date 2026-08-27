import sys
import os

# Add the project root to the Python path so we can import backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from a2a.types import AgentCard, Task, Message, Role, Part
from backend.agents.base_agent import TaskResult
from backend.policies.engine import PolicyEngine

def test_a2a_models():
    print("--- Testing A2A Models ---")
    
    # Test AgentCard creation
    card = AgentCard(
        name="Adventure Gear Merchant",
        description="Sells premium outdoor gear."
    )
    print(f"✅ AgentCard Created: {card.name}")

    # Test Task & Message creation
    task = Task(
        id="task-123",
        history=[
            Message(role=Role.ROLE_USER, parts=[Part(text="I want to buy a tent.")])
        ]
    )
    print(f"✅ Task Created: {task.id}")
    
    # Test TaskResult creation
    result = TaskResult(
        task_id=task.id,
        status="completed",
        result_data={"order_id": "order_xyz123"}
    )
    print(f"✅ TaskResult Created: status {result.status}")
    print("--------------------------\n")

def test_policy_engine():
    print("--- Testing Policy Engine ---")
    
    # 1. Test Valid Cart
    cart = [
        {"price": 5000.0, "quantity": 2}, # ₹10,000 total
    ]
    is_valid, msg = PolicyEngine.validate_cart(cart, applied_discount=5.0)
    print(f"Valid Cart (5% discount, ₹10k total): {'✅' if is_valid else '❌'} - {msg}")
    
    # 2. Test Invalid Discount (> 10%)
    is_valid, msg = PolicyEngine.validate_cart(cart, applied_discount=15.0)
    print(f"Invalid Discount (15%): {'✅' if not is_valid else '❌'} - {msg}")
    
    # 3. Test Invalid Quantity (> 10 items)
    cart_high_qty = [
        {"price": 500.0, "quantity": 15}, 
    ]
    is_valid, msg = PolicyEngine.validate_cart(cart_high_qty)
    print(f"Invalid Quantity (15 items): {'✅' if not is_valid else '❌'} - {msg}")
    
    # 4. Test Invalid Transaction Total (> ₹50,000)
    cart_high_value = [
        {"price": 30000.0, "quantity": 2}, # ₹60,000 total
    ]
    is_valid, msg = PolicyEngine.validate_cart(cart_high_value)
    print(f"Invalid Transaction Total (₹60k): {'✅' if not is_valid else '❌'} - {msg}")
    
    # 5. Test Refund Limit (> ₹5,000)
    is_valid, msg = PolicyEngine.check_refund_request(6000.0)
    print(f"Refund Request (₹6k > ₹5k limit): {'✅' if not is_valid else '❌'} - {msg}")
    print("--------------------------\n")

if __name__ == "__main__":
    test_a2a_models()
    test_policy_engine()
