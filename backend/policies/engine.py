from typing import Dict, Any, Tuple, List

# Hardcoded Business Rules ("The Bar")
MAX_DISCOUNT_PERCENT = 10.0
MAX_TRANSACTION_VALUE_INR = 50000.0
MAX_QUANTITY_PER_ITEM = 10
REQUIRES_HUMAN_APPROVAL_REFUND_AMOUNT = 5000.0

class PolicyViolation(Exception):
    """Exception raised when a deterministic policy is violated."""
    pass

class PolicyEngine:
    """
    Deterministic Safety Gate for the Merchant Agent System.
    Enforces business rules with 100% Python code (no LLMs).
    """

    @staticmethod
    def check_discount(requested_discount_percent: float) -> Tuple[bool, str]:
        """Ensures the discount does not exceed the maximum allowed."""
        if requested_discount_percent > MAX_DISCOUNT_PERCENT:
            return False, f"Requested discount of {requested_discount_percent}% exceeds the maximum allowed {MAX_DISCOUNT_PERCENT}%."
        return True, "Discount approved."

    @staticmethod
    def check_transaction_limit(total_value: float) -> Tuple[bool, str]:
        """Ensures the transaction value does not exceed the maximum allowed."""
        if total_value > MAX_TRANSACTION_VALUE_INR:
            return False, f"Transaction value of ₹{total_value} exceeds the automated limit of ₹{MAX_TRANSACTION_VALUE_INR}. Escalating to human."
        return True, "Transaction limit check passed."

    @staticmethod
    def check_quantity_limit(quantity: int) -> Tuple[bool, str]:
        """Ensures the quantity per item does not exceed the maximum allowed."""
        if quantity > MAX_QUANTITY_PER_ITEM:
            return False, f"Quantity of {quantity} exceeds the automated per-item limit of {MAX_QUANTITY_PER_ITEM}."
        return True, "Quantity check passed."

    @staticmethod
    def check_refund_request(refund_amount: float) -> Tuple[bool, str]:
        """Checks if a refund request requires human approval."""
        if refund_amount > REQUIRES_HUMAN_APPROVAL_REFUND_AMOUNT:
            return False, f"Refunds over ₹{REQUIRES_HUMAN_APPROVAL_REFUND_AMOUNT} require explicit human approval. Escalating to store manager."
        return True, "Refund within automated limits."
        
    @staticmethod
    def validate_cart(cart_items: List[Dict[str, Any]], applied_discount: float = 0.0) -> Tuple[bool, str]:
        """
        Validates an entire cart against all policies.
        cart_items should be a list of dicts containing 'price' and 'quantity'.
        """
        # 1. Check Discount
        is_valid, msg = PolicyEngine.check_discount(applied_discount)
        if not is_valid:
            return is_valid, msg
            
        total_value = 0.0
        for item in cart_items:
            # 2. Check Quantity
            qty = item.get('quantity', 1)
            is_valid, msg = PolicyEngine.check_quantity_limit(qty)
            if not is_valid:
                return is_valid, msg
                
            total_value += item.get('price', 0.0) * qty
            
        # Apply discount to total value
        total_value = total_value * (1 - (applied_discount / 100))
        
        # 3. Check Transaction Limit
        is_valid, msg = PolicyEngine.check_transaction_limit(total_value)
        if not is_valid:
            return is_valid, msg
            
        return True, "Cart passes all deterministic policies."
