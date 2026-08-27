import os
import razorpay
from dotenv import load_dotenv

load_dotenv()
key_id = os.getenv("RAZORPAY_KEY_ID")
key_secret = os.getenv("RAZORPAY_KEY_SECRET")

client = razorpay.Client(auth=(key_id, key_secret))
try:
    link = client.payment_link.create({
        "amount": 1000,
        "currency": "INR",
        "description": "Test Link",
        "customer": {
            "name": "Test User",
            "email": "test@example.com",
            "contact": "+919876543210"
        }
    })
    print(f"Success! Link: {link['short_url']}")
except Exception as e:
    print(f"Error: {e}")
