import os
from flask import Flask
from twilio.rest import TwilioRestClient
from pymongo import Connection

app = Flask(__name__)

# Twilio details
account = "AC74068c46306d722c23fc68291b67071a"
token = "da09cf1ce50760e7ef4405d9c8334239"
client = TwilioRestClient(account, token)

# Connect to MongoDB, and retrieve collections
MONGO_URL = os.environ.get('MONGOHQ_URL')


@app.route('/')
def hello():
	connection = Connection(MONGO_URL)
	db = connection.app7324197
	
	users = db.users
	payments = db.payments
	
	return "Hello, world!"
	
	
	for message in client.sms.messages.list():
	    print message.body

	message = client.sms.messages.create(to="+14254436511", from_="+14259678372",
	                                     body="Hello there!")
	
	#return output

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)