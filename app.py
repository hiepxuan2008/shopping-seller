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

def send_generic_template(sender_id, elements):
    data = json.dumps({
        "recipient": {
            "id": sender_id
        },
        "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "elements": elements
                }
            }
        }
    })
    call_send_api(data)

def response_go_shopping(sender_id):
    elements = [{
        "title": "Nice Blue T-Shirt - $19.99",
        "item_url": "http://www.lazada.vn/ao-thun-nam-co-tru-xanh-navi-2035572.html",
        "image_url": "http://vn-live-02.slatic.net/p/ao-thun-nam-co-tru-xanh-co-vit-1405-3755302-0a0daa09d238345d6a267ba403f7abbe-catalog_233.jpg",
        "buttons": [
            {
                "type": "web_url",
                "url": "http://www.lazada.vn/ao-thun-nam-co-tru-xanh-navi-2035572.html",
                "title": "View item"
            }
        ]
    },
        {
            "title": "Light Green T-Shirt - $21.99",
            "item_url": "http://zanado.com/ao-thun-nam-jackies-b202-dep-gia-re-sid48907.html?color=98",
            "image_url": "http://a4vn.com/media/catalog/product/cache/all/thumbnail/255x298/7b8fef0172c2eb72dd8fd366c999954c/1/3/13_40_2.jpg",
            "buttons": [
                {
                    "type": "web_url",
                    "url": "http://zanado.com/ao-thun-nam-jackies-b202-dep-gia-re-sid48907.html?color=98",
                    "title": "View item"
                }
            ]
        },
        {
            "title": "Raglan T-Shirt red & white- $12.99",
            "item_url": "http://www.lazada.vn/ao-thun-nam-tay-raglan-do-do-phoi-trang-2056856.html?mp=1",
            "image_url": "http://vn-live-01.slatic.net/p/ao-thun-nam-tay-raglan-do-do-phoi-trang-2581-6586502-2d977472b068b70467eeb4e9d2e1122d-catalog_233.jpg",
            "buttons": [
                {
                    "type": "web_url",
                    "url": "http://www.lazada.vn/ao-thun-nam-tay-raglan-do-do-phoi-trang-2056856.html?mp=1",
                    "title": "View item"
                }
            ]
        }]

    send_generic_template(sender_id, elements)


def response_shop_location(recipient_id):
    elements = [
        {
            'title': "Nova Shop",
            'subtitle': "227 Nguyen Van Cu, D5, HCM city",
            'image_url': 'http://staticmap.openstreetmap.de/staticmap.php?center=10.762952,106.682340&zoom=15&size=640x480&markers=10.762952,106.682340,ol-marker',
            'buttons': [{
                'type': 'web_url',
                'url': 'http://maps.google.com/maps?q=loc:10.762952,106.682340&z=20',
                'title': "Show directions"
            }
            ]
        }
    ]
    send_generic_template(recipient_id, elements)
    pass


def response_call_for_help(recipient_id):
    phone_number = "+84983892316"
    buttons = [
        {
            "type": "phone_number",
            "title": phone_number,
            "payload": phone_number
        }
    ]
    send_button_template(recipient_id, "Make a phone call", buttons)


def send_button_template(recipient_id, text, buttons):
    data = json.dumps({
      "recipient":{
        "id":recipient_id
      },
      "message":{
        "attachment":{
          "type":"template",
          "payload":{
            "template_type":"button",
            "text":text,
            "buttons":buttons
          }
        }
      }
    })
    call_send_api(data)

def on_postback_received(sender_id, payload):
    if payload == "GO_SHOPPING":
        response_go_shopping(sender_id)
    elif payload == "SHOP_LOCATION":
        response_shop_location(sender_id)
    elif payload == "CALL_FOR_HELP":
        response_call_for_help(sender_id)

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
