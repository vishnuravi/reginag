from config import *
from flask import Flask, request, redirect, render_template
from watson_developer_cloud import ToneAnalyzerV3Beta
from pymongo import MongoClient
import requests
import twilio.twiml
import json
import apiai
import uuid
import datetime

app = Flask(__name__)

client = MongoClient()
db = client.reginag

@app.route("/")
def hello():
   return render_template('hello.html')

@app.route("/get_text/<id>")
def get_text(id):
   return concatenate_session(id)
   
@app.route("/get_score/<id>")
def get_score(id):
	score = db.results.find_one({"session_id": id})
	return str(score['confidence'])

@app.route("/sms", methods=['GET', 'POST'])
def process_sms():
    """ Processes messages coming in via Twilio """
    phone_number = request.values.get('From', None)
    sms_message = request.values.get('Body', None)
    resp = twilio.twiml.Response()
    regina_answer = ask_regina(phone_number, sms_message, "sms")['text']
    resp.message(regina_answer)
    return str(resp)
    
def reply(user_id, msg):
    data = {
        "recipient": {"id": user_id},
        "message": {"text": msg}
    }
    resp = requests.post("https://graph.facebook.com/v2.6/me/messages?access_token=" + FB_PAGE_ACCESS_TOKEN, json=data)
    print(resp.content)

def reply_with_img(user_id, img_url):
    data = {
        "recipient": {"id": user_id},
        "message": {"attachment":{ "type":"image", "payload": {"url": img_url} } }
    }
    resp = requests.post("https://graph.facebook.com/v2.6/me/messages?access_token=" + FB_PAGE_ACCESS_TOKEN, json=data)
    print(resp.content)

@app.route('/fb', methods=['POST'])
def handle_incoming_messages():
    data = request.json
    sender = data['entry'][0]['messaging'][0]['sender']['id']
    message = data['entry'][0]['messaging'][0]['message']['text']
    response = ask_regina(sender, message, "fb")
    regina_answer = response['text']
    intent = response['intent']
    reply(sender, regina_answer)
    return regina_answer

@app.route('/fb', methods=['GET'])
def handle_verification():
    return request.args['hub.challenge']

def ask_regina(sender_id, message, route):
    #identify the current session
    session_id = find_session(sender_id)
    
    #query Api.ai
    ai = apiai.ApiAI(APIAI_CLIENT_ACCESS_TOKEN, APIAI_SUBSCRIPTION_KEY)
    ai_request = ai.text_request()
    ai_request.query = message
    ai_response = ai_request.getresponse()
    response_dict = json.loads(ai_response.read())
    regina_text = response_dict['result']['fulfillment']['speech']
    
    #check if an intent was identified by api.ai
    try:
        regina_intent = response_dict['result']['metadata']['intentName']
    except KeyError:
        regina_intent = "none"

    #if Bye intent, analyze tone and close session
    if regina_intent == "Bye":
        conversation = concatenate_session(session_id)
        if conversation != "":
            confidence = analyze_tone(conversation)
            db.results.insert_one({'session_id': session_id, "confidence": confidence})
            if confidence < CONFIDENCE_THRESHOLD:
                regina_text = "Your confidence score was " + str(confidence) + ". You weren't very confident :( "
                if route == "fb":
                    reply_with_img(sender_id, UNCONFIDENT_IMAGE)
            else:
                regina_text = "Your confidence score was " + str(confidence) + ". You really stood up to me!"
                if route == "fb":
                    reply_with_img(sender_id, CONFIDENT_IMAGE)
            regina_text += " Click here to find out more about how you did - " + REPORT_BASE_URL + session_id 
            close_session(session_id)
        else:
            regina_text = "Bye!"
    else:
        #log message and response to db
        db.messages.insert_one({'createdAt': datetime.datetime.utcnow(), 'sender_id': sender_id, 'session_id': session_id, 'message': message, 'response': regina_text})

    return {'text' : regina_text, 'intent' : regina_intent}

def find_session(sender_id):
    """ Checks if a session exists for the given sender id, else create a new one """
    session = db.sessions.find_one({'sender_id': sender_id})
    if session is None:    
        session_id = str(uuid.uuid4())
        db.sessions.insert_one({'createdAt': datetime.datetime.utcnow(), 'sender_id': sender_id, 'session_id': session_id})
    else:
        session_id = session['session_id']
    return session_id
    
def close_session(session_id):
    """Deletes the session with the given id"""
    db.sessions.remove({'session_id': session_id})
    
def concatenate_session(session_id):
    """Concatenates all messages in the session"""
    conversation = ""
    for msg in db.messages.find({'session_id': session_id}):
        conversation += (msg['message'] + "\n") 
    return conversation
    
def analyze_tone(conversation):
    """ Take conversation text and calculates the confidence score using Watson Tone Analyzer """
    tone_analyzer = ToneAnalyzerV3Beta(username=WATSON_USERNAME,password=WATSON_PASSWORD,version=WATSON_API_VERSION)
    tone_response = tone_analyzer.tone(conversation)
    confidence = tone_response['document_tone']['tone_categories'][1]['tones'][1]['score']
    return confidence

if __name__ == "__main__":
    app.run(host='0.0.0.0')
