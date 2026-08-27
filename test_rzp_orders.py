import os
import razorpay
from dotenv import load_dotenv

load_dotenv()
key_id = os.getenv("RAZORPAY_KEY_ID")
key_secret = os.getenv("RAZORPAY_KEY_SECRET")

client = razorpay.Client(auth=(key_id, key_secret))
orders = client.order.fetch_all()
print(f"Found {orders['count']} orders in Razorpay.")
if orders['count'] > 0:
    print(f"Latest order ID: {orders['items'][0]['id']}, amount: {orders['items'][0]['amount']}, receipt: {orders['items'][0]['receipt']}")
