import os
import hmac
import hashlib
import logging
from typing import Dict, Any

try:
    import razorpay
except ImportError:
    razorpay = None

logger = logging.getLogger(__name__)

class RazorpayClient:
    """
    Wrapper for the Razorpay API.
    Handles test mode and graceful fallbacks if keys are missing.
    """
    def __init__(self):
        self.key_id = os.getenv("RAZORPAY_KEY_ID")
        self.key_secret = os.getenv("RAZORPAY_KEY_SECRET")
        
        self.is_mock = False
        if not self.key_id or not self.key_secret or not razorpay or 'dummy' in self.key_id or 'dummy' in self.key_secret:
            logger.warning("Razorpay credentials missing, dummy, or razorpay package not installed. Running in MOCK mode.")
            self.is_mock = True
            self.client = None
        else:
            self.client = razorpay.Client(auth=(self.key_id, self.key_secret))

    def create_order(self, amount: int, currency: str = "INR", receipt: str = "", notes: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Create a Razorpay order.
        Amount must be in paise (e.g. ₹10 = 1000 paise).
        """
        if self.is_mock:
            logger.info(f"[MOCK] Created Razorpay order for {amount} {currency}")
            return {
                "id": f"mock_order_{receipt}",
                "amount": amount,
                "currency": currency,
                "receipt": receipt,
                "status": "created",
                "notes": notes or {}
            }
            
        data = {
            "amount": amount,
            "currency": currency,
            "receipt": receipt,
            "notes": notes or {}
        }
        
        try:
            order = self.client.order.create(data=data)
            return order
        except Exception as e:
            logger.error(f"Failed to create Razorpay order: {e}")
            raise Exception(f"Razorpay order creation failed: {str(e)}")

    def verify_payment(self, order_id: str, payment_id: str, signature: str) -> bool:
        """
        Verify the Razorpay payment signature.
        """
        if self.is_mock:
            logger.info(f"[MOCK] Verified payment {payment_id} for order {order_id}")
            # In mock mode, we assume payment_id != 'decline' means success.
            # We can use this to simulate declines by passing 'decline' as payment_id
            if "decline" in payment_id.lower():
                return False
            return True
            
        try:
            params_dict = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
            # verify_payment_signature returns None on success, raises error on failure
            self.client.utility.verify_payment_signature(params_dict)
            return True
        except Exception as e:
            logger.error(f"Payment verification failed: {e}")
            return False

    def create_payment_link(self, amount: int, currency: str = "INR", description: str = "", customer_details: Dict[str, str] = None, reference_id: str = "") -> Dict[str, Any]:
        """
        Create a Razorpay Payment Link.
        """
        if self.is_mock:
            import uuid
            mock_id = f"mock_plink_{uuid.uuid4().hex[:8]}"
            logger.info(f"[MOCK] Created Payment Link {mock_id} for {amount} {currency}")
            return {
                "id": mock_id,
                "short_url": f"https://mock.rzp.io/{mock_id}",
                "status": "created",
                "reference_id": reference_id
            }

        data = {
            "amount": amount,
            "currency": currency,
            "description": description,
            "reference_id": reference_id,
            "customer": customer_details or {},
            "notify": {"sms": False, "email": False},
            "reminder_enable": False
        }

        try:
            link = self.client.payment_link.create(data)
            return link
        except Exception as e:
            logger.error(f"Failed to create Payment Link: {e}")
            raise Exception(f"Razorpay Payment Link creation failed: {str(e)}")

    def verify_payment_link_status(self, payment_link_id: str) -> str:
        """
        Check the status of a Payment Link.
        Returns the status string (e.g., 'paid', 'created', 'cancelled').
        """
        if self.is_mock:
            logger.info(f"[MOCK] Fetched status for Payment Link {payment_link_id}")
            # If it's a mock, we just say paid to simulate successful manual checkout
            return "paid"

        try:
            link = self.client.payment_link.fetch(payment_link_id)
            return link.get("status", "unknown")
        except Exception as e:
            logger.error(f"Failed to fetch Payment Link status: {e}")
            return "failed"

