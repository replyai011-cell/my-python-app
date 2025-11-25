import os
import requests
from flask import Flask, request
from openai import OpenAI

# Environment variables
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
OPENAI_KEY = os.environ.get("OPENAI_KEY")

client = OpenAI(api_key=OPENAI_KEY)

app = Flask(__name__)

SELLER_BRAIN = """
You are an AI sales assistant for a Facebook Marketplace seller.
Keep replies short, friendly, and direct (1–3 sentences).

Seller inventory categories:
- Cars, trucks, motorcycles
- ATVs, dirt bikes, jet skis, boats
- Car parts (OEM + aftermarket)
- Trailers, lawn mowers, power equipment
- House appliances (fridge, washer, dryer, stove)
- Furniture (beds, couches, dressers)
- Tools (hand tools, power tools)

General rules:
1. ALWAYS answer “Yes, still available” if they ask about availability.
2. If they ask for price, repeat the listed price and remind it's firm unless seller says otherwise.
3. If they ask for lowest price → say “Price is firm but you can check it out in person.”
4. If they ask about condition → give a short general condition: “Good condition, works great.”
5. ALWAYS ask: “When would you like to come see it / pick it up?”
6. Never give exact address unless seller provides it; instead say: “Pickup in Parma, OH.”
7. Keep it polite, simple, and fast—no long paragraphs.
"""

# ------------------------------
# Send Message to Facebook API
# ------------------------------
def send_message(recipient_id, msg_text):
    url = "https://graph.facebook.com/v21.0/me/messages"
    params = {"access_token": PAGE_ACCESS_TOKEN}
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": msg_text}
    }
    requests.post(url, params=params, json=payload)


# ------------------------------
# GET - Facebook webhook verify
# ------------------------------
@app.route('/', methods=['GET'])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Verification failed"


# ------------------------------
# POST - Facebook webhook messages
# ------------------------------
@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()

    if "entry" in data:
        for entry in data["entry"]:
            if "messaging" in entry:
                for event in entry["messaging"]:
                    if "message" in event:
                        sender_id = event["sender"]["id"]
                        user_message = event["message"].get("text", "")

                        # Generate AI reply
                        response = client.chat.completions.create(
                            model="gpt-4.1-mini",
                            messages=[
                                {"role": "system", "content": SELLER_BRAIN},
                                {"role": "user", "content": user_message}
                            ],
                        )

                        ai_reply = response.choices[0].message.content

                        # Send response back to user
                        send_message(sender_id, ai_reply)

    return "ok"
