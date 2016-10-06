import os
import sys
import json

import requests
from flask import Flask, request

app = Flask(__name__)


@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must
    # return the 'hub.challenge' value in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200

@app.route('/', methods=['POST'])
def webhook():

    # endpoint for processing incoming messaging events

    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing

    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                # https://developers.facebook.com/docs/messenger-platform/webhook-reference/message-received
                if messaging_event.get("message"):  # someone sent us a message
                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    message = messaging_event["message"] # message from user
                    on_message_received(sender_id, message)

                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                # https://developers.facebook.com/docs/messenger-platform/webhook-reference/postback-received
                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    sender_id = messaging_event["sender"]["id"]  # the facebook ID of the person sending you the message
                    payload = messaging_event["postback"]["payload"]  # payload from user
                    on_postback_received(sender_id, payload)

    return "ok", 200

def on_message_received(sender_id, message):
    if not message.get("text"):
        return

    send_typing_on(sender_id)
    message_text = message["text"]
    if message_text == "help":
        send_response_help(sender_id)
    else:
        send_text_message(sender_id, "Invalid command, please send hello")

def on_postback_received(sender_id, payload):

    pass

def send_response_help(recipient_id):
    data = json.dumps({
      "recipient":{
        "id":recipient_id
      },
      "message":{
        "attachment":{
          "type":"template",
          "payload":{
            "template_type":"button",
            "text":"Hi, Can I help you?",
            "buttons":[
                {
                    "type": "postback",
                    "title": "Go Shopping",
                    "payload": "GO_SHOPPING"
                },
                {
                    "type": "postback",
                    "title": "Shop Location",
                    "payload": "SHOP_LOCATION"
                },
                {
                    "type": "postback",
                    "title": "Call For Help",
                    "payload": "CALL_FOR_HELP"
                }
            ]
          }
        }
      }
    })

    call_send_api(data)

def send_typing_on(recipient_id):
    data = json.dumps({
      "recipient":{
        "id":recipient_id
      },
      "sender_action":"typing_on"
    })

    call_send_api(data)

# Send Message
# https://developers.facebook.com/docs/messenger-platform/send-api-reference/text-message
def send_text_message(recipient_id, message_text):
    data = json.dumps({
      "recipient":{
        "id":recipient_id
      },
      "message":{
        "text":message_text
      }
    })
    call_send_api(data)

# Response to Facebook Messenger API
def call_send_api(data):
    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)

# Simple wrapper for logging to stdout on heroku
def log(message):
    print str(message)
    sys.stdout.flush()

# Main app
if __name__ == '__main__':
    app.run(debug=True)
