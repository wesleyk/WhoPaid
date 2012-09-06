import os
from flask import Flask, request, redirect
from twilio.rest import TwilioRestClient
from pymongo import Connection

app = Flask(__name__)

MONGO_URL = os.environ.get('MONGOHQ_URL')

@app.route('/', methods=['GET', 'POST'])
def parseSMS():
	# Twilio details
	account = "AC74068c46306d722c23fc68291b67071a"
	token = "da09cf1ce50760e7ef4405d9c8334239"
	client = TwilioRestClient(account, token)
	
	# Connect to MongoDB, and retrieve collections
	connection = Connection(MONGO_URL)
	db = connection.app7324197
	
	users = db.users
	payments = db.payments
	
	from_number = request.values.get('From', None)
	body = request.values.get('Body', None)
	
	# Wesley sent in message
	if (from_number == "+14254436511"):
		body += "Wesley"
	
	# Brandon sent in message
	elif (from_number == "+19256837230"):
		body += "Brandon"
	
	# Eddie sent in message
	elif (from_number == "+15615426296"):
		body += "Eddie"
	
	# ignore message because it wasn't from one of us
	else:
		body += "Not part of the land down Unger"
	
	body += from_number
	
	message = client.sms.messages.create(to=from_number, from_="+14259678372", body=body)

	return ""
	
if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)