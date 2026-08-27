import os
import httpx
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

class BuyerAgent:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    def process_goal(self, goal: str, log_callback):
        """
        Process a high-level user goal by autonomously communicating with the Merchant.
        `log_callback(role, message)` is called to stream updates to the UI.
        """
        system_instruction = """
        You are an autonomous Buyer Agent representing a user. Your goal is to negotiate and buy items from the Merchant Orchestrator.
        You are acting on behalf of John Doe. Your details are:
        - Email: john@example.com
        - Phone: +919876543210
        - Address: 123 Outdoor Lane, Bangalore
        
        You will be provided with the user's high-level goal.
        You have a tool to send messages to the Merchant Orchestrator. Use it to communicate, search for items, ask about policies, and checkout.
        When you are ready to checkout, you MUST explicitly provide your name, email, phone, and address to the Merchant.
        The merchant will respond with a Payment Link. You must wait for the human user to complete the payment. 
        Once the system tells you the user has paid, you must tell the merchant to verify the payment.
        When you send a message, it will automatically be prefixed with the correct Merchant and Session context, so just write the natural language message (e.g., "What tents do you have?").
        You must wait for the merchant's response before sending your next message.
        When the goal is fully achieved (e.g. checkout is complete and payment is successful), output "GOAL ACHIEVED" followed by a summary of the outcome.
        """

        def send_message_to_merchant(message: str) -> str:
            """Sends a message to the Merchant Orchestrator to fulfill the user's goal."""
            log_callback("buyer", message)
            
            # The backend expects the context in the intent string based on Phase 6 tests
            intent_msg = f"Context: Merchant=merch_adventurehub, Session=buyer_session. {message}"
            
            jsonrpc_payload = {
                "jsonrpc": "2.0",
                "method": "SendMessage",
                "params": {
                    "message": {
                        "role": "ROLE_USER",
                        "parts": [{"text": intent_msg}]
                    },
                    "metadata": {
                        "session_id": "buyer_session"
                    }
                },
                "id": "1"
            }
            try:
                with httpx.Client(timeout=60.0) as client:
                    resp = client.post(
                        f"{self.base_url}/api/jsonrpc",
                        json=jsonrpc_payload,
                        headers={"A2A-Version": "1.0"}
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    
                    if "error" in data:
                        error_msg = f"RPC Error: {data['error']}"
                        log_callback("system", error_msg)
                        return error_msg
                        
                    result_msg = data.get("result", {}).get("message", {}).get("parts", [{}])[0].get("text", "No response text")
                    log_callback("merchant", result_msg)
                    
                    if "rzp.io" in result_msg:
                        import webbrowser
                        import re
                        match = re.search(r'(https://rzp\.io/\S+)', result_msg)
                        if match:
                            url = match.group(1).rstrip('.')
                            print(f"\n\033[92m*** RAZORPAY CHECKOUT OPENED ***\033[0m")
                            print(f"URL: {url}")
                            print("Please complete the payment in your browser using a test card.")
                            webbrowser.open(url)
                            input("\nPress ENTER once you have completed the payment...")
                            result_msg += "\n\n[SYSTEM]: The human user has successfully paid the link in their browser. You may now tell the merchant the payment is completed."
                            
                    return result_msg
            except Exception as e:
                error_msg = f"Error communicating with merchant: {e}"
                log_callback("system", error_msg)
                return error_msg

        chat = self.client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.0,
                tools=[send_message_to_merchant],
            )
        )
        
        log_callback("system", f"Starting to process goal: {goal}")
        response = chat.send_message(f"User Goal: {goal}")
        
        log_callback("system", "Agent execution finished.")
        try:
            text = response.text
            return text if text else "Agent finished (No text response)"
        except ValueError:
            return "Agent finished (Returned a non-text response, e.g. function call)"
