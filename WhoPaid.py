import os
from flask import Flask, request, redirect
from twilio.rest import TwilioRestClient
from pymongo import Connection

app = Flask(__name__)

# MongoDB url
MONGO_URL = os.environ.get('MONGOHQ_URL')

# Twilio details
account = "AC74068c46306d722c23fc68291b67071a"	  	
token = "da09cf1ce50760e7ef4405d9c8334239"
twilio_number = "+14259678372"

# Name constants
w = "Wesley"
b = "Brandon"
e = "Eddie"

# Our phone numbers
w_number = "+14254436511"
b_number = "+19256837230"
e_number = "+15615426296"

# Used to show current balance
# Only displays >0 values
def generateBalance(w_owes,b_owes,e_owes):
	response = ""
	
	if(w_owes[b] > 0):
		response += "w owes b: " + str(w_owes[b]) + "\n"
	if(w_owes[e] > 0):
		response += "w owes e: " + str(w_owes[e]) + "\n"
	if(b_owes[w] > 0):
		response += "b owes w: " + str(b_owes[w]) + "\n"
	if(b_owes[e] > 0):	
		response += "b owes e: " + str(b_owes[e]) + "\n"
	if(e_owes[w] > 0):
		response += "e owes w: " + str(e_owes[w]) + "\n"
	if(e_owes[b] > 0):
		response += "e owes b: " + str(e_owes[b]) + "\n"
		
	return response
	

@app.route('/', methods=['POST'])
def parseSMS():
	# Establish connection with Twilio
	client = TwilioRestClient(account, token)
	
	# Connect to MongoDB, and retrieve collections
	connection = Connection(MONGO_URL)
	db = connection.app7324197
	
	users = db.users
	payments = db.payments

	# Determine current debts
	w_doc = users.find_one({"username":w})
	w_owes = w_doc["owes"]
	b_doc = users.find_one({"username":b})
	b_owes = b_doc["owes"]
 	e_doc = users.find_one({"username":e})
	e_owes = e_doc["owes"]
	
	# Parse message for sender, amount, and target
	from_number = request.values.get('From', None)
	body = request.values.get('Body', None)
	
	body_array = body.split(" ")
	response = ""
	
	# empty text case
	if (len(body_array) == 0):
		return ""
	
	# respond to RETRIEVE BALANCE TEXT
	
	if (body_array[0].lower()[:3] == "bal"):
		response = generateBalance(w_owes,b_owes,e_owes)
		client.sms.messages.create(to=from_number, from_=twilio_number, body=response)
		return ""
	
	# if first element is not a number, return error
	if (type(body_array[0]) == float or type(body_array[0]) == int):
		response = "Must text in 'bal' or an amount"
		client.sms.messages.create(to=from_number, from_=twilio_number, body=response)
		return ""
	
	# respond to SUBMIT PAYMENT TEXT
	
	# determine amount paid, rounded to two decimal points
	amount = round(float(body_array[0]), 2)

	# if amount is negative, return error
	if(amount <= 0):
		response = "Must text in positive amount"
		client.sms.messages.create(to=from_number, from_=twilio_number, body=response)
		return ""
	
	# determine how much each person should contribute
	# it's either 1/3 amount if it's a payment for everyone,
	# or just amount if it's a payment from one person to another
	amount_charged = amount
	
	# determine if the payment is for all members
	pay_all = len(body_array) == 1
	if(pay_all):
		amount_charged = amount / 3

	# Wesley sent in message
	if (from_number == w_number):
		# Register payment
		if(pay_all):
			payments.insert({"Amount":amount,"From":w,"To":"All"})
			response = "w paid " + amount "\n"
		else:
			payments.insert({"Amount":amount,"From":w,"To":body_array[1]})
			response = "w paid " + body_array[1] + " " + amount "\n"
		
		# pay Brandon case
		if (pay_all or body_array[1] == "b"):
			# Wesley owes Brandon case
			if (w_owes[b] > 0):
				# Wesley owes Brandon more than he just paid, so deduct the amount paid from the total
				if (w_owes[b] >= amount_charged):
					w_owes[b] -= amount_charged
				# Wesley owes Brandon less than he just paid, so now Brandon owes Wesley some money
				else:
					b_owes[w] = amount_charged - w_owes[b] 
					w_owes[b] = 0
			# Brandon owes Wesley case
			elif (b_owes[w] >= 0):
				b_owes[w] += amount_charged

		# pay Eddie case
		if (pay_all or body_array[1] == "e"):
			# Wesley owes Eddie case
			if (w_owes[e] > 0):
				# Wesley owes Eddie more than he just paid, so deduct the amount paid from the total
				if (w_owes[e] >= amount_charged):
					w_owes[e] -= amount_charged
				# Wesley owes Eddie less than he just paid, so now Eddie owes Wesley some money
				else:
					e_owes[w] = amount_charged - w_owes[e] 
					w_owes[e] = 0
			# Eddie owes Wesley case
			elif (e_owes[w] >= 0):
				e_owes[w] += amount_charged
				
	# Brandon sent in message
	elif (from_number == b_number):
		# Register payment
		if(pay_all):
			payments.insert({"Amount":amount,"From":b,"To":"All"})
			response = "b paid " + amount "\n"
		else:
			payments.insert({"Amount":amount,"From":b,"To":body_array[1]})
			response = "b paid " + body_array[1] + " " + amount "\n"
			
		# pay Wesley case
		if (pay_all or body_array[1] == "w"):
			# Brandon owes Wesley case
			if (b_owes[w] > 0):
				# Brandon owes Wesley more than he just paid, so deduct the amount paid from the total
				if (b_owes[w] >= amount_charged):
					b_owes[w] -= amount_charged
				# Brandon owes Wesley less than he just paid, so now Wesley owes Brandon some money
				else:
					w_owes[b] = amount_charged - b_owes[w] 
					b_owes[w] = 0
			# Wesley owes Brandon case
			elif (w_owes[b] >= 0):
				w_owes[b] += amount_charged

		# pay Eddie case
		if (pay_all or body_array[1] == "e"):
			# Brandon owes Eddie case
			if (b_owes[e] > 0):
				# Brandon owes Eddie more than he just paid, so deduct the amount paid from the total
				if (b_owes[e] >= amount_charged):
					b_owes[e] -= amount_charged
				# Brandon owes Eddie less than he just paid, so now Eddie owes Brandon some money
				else:
					e_owes[b] = amount_charged - b_owes[e] 
					b_owes[e] = 0
			# Eddie owes Brandon case
			elif (e_owes[b] >= 0):
				e_owes[b] += amount_charged


	# Eddie sent in message
	elif (from_number == e_number):
		# Register payment
		if(pay_all):
			payments.insert({"Amount":amount,"From":e,"To":"All"})
			response = "e paid " + amount "\n"
		else:
			payments.insert({"Amount":amount,"From":e,"To":body_array[1]})
			response = "e paid " + body_array[1] + " " + amount "\n"
			
		# pay Wesley case
		if (pay_all or body_array[1] == "w"):
			# Eddie owes Wesley case
			if (e_owes[w] > 0):
				# Eddie owes Wesley more than he just paid, so deduct the amount paid from the total
				if (e_owes[w] >= amount_charged):
					e_owes[w] -= amount_charged
				# Eddie owes Wesley less than he just paid, so now Wesley owes Eddie some money
				else:
					w_owes[e] = amount_charged - e_owes[w] 
					e_owes[w] = 0
			# Wesley owes Eddie case
			elif (w_owes[e] >= 0):
				w_owes[e] += amount_charged
				
		# pay Brandon case
		if (pay_all or body_array[1] == "b"):
			# Eddie owes Brandon case
			if (e_owes[b] > 0):
				# Eddie owes Brandon more than he just paid, so deduct the amount paid from the total
				if (e_owes[b] >= amount_charged):
					e_owes[b] -= amount_charged
				# Eddie owes Brandon less than he just paid, so now Brandon owes Eddie some money
				else:
					b_owes[e] = amount_charged - e_owes[b] 
					e_owes[b] = 0
			# Brandon owes Eddie case
			elif (b_owes[e] >= 0):
				b_owes[e] += amount_charged
				
	# ignore message because it wasn't from one of us
	else:
		response = "Not part of the land down Unger"
		client.sms.messages.create(to=from_number, from_=twilio_number, body=response)
		return ""
	
	# reduce any circular debts
	# eg: E owes W x, W owes B y, so E should owe B x and W should owe B y - x,
	# although cased on whether x >= y
	if (w_owes[b] > 0 and b_owes[e] > 0):
		if(w_owes[b] >= b_owes[e]):
			w_owes[e] += b_owes[e]
			w_owes[b] -= b_owes[e]
			b_owes[e] = 0
		else:
			w_owes[e] += w_owes[b]
			b_owes[e] -= w_owes[b]
			w_owes[b] = 0
		
	if (w_owes[e] > 0 and e_owes[b] > 0):
		if(w_owes[e] >= e_owes[b]):
			w_owes[b] += e_owes[b]
			w_owes[e] -= e_owes[b]
			e_owes[b] = 0
		else:
			w_owes[b] += w_owes[e]
			e_owes[b] -= w_owes[e]
			w_owes[e] = 0
		
	if (b_owes[w] > 0 and w_owes[e] > 0):
		if(b_owes[w] >= w_owes[e]):
			b_owes[e] += w_owes[e]
			b_owes[w] -= w_owes[e]
			w_owes[e] = 0
		else:
			b_owes[e] += b_owes[w]
			w_owes[e] -= b_owes[w]
			b_owes[w] = 0

	if (b_owes[e] > 0 and e_owes[w] > 0):
		if(b_owes[e] >= e_owes[w]):
			b_owes[w] += e_owes[w]
			b_owes[e] -= e_owes[w]
			e_owes[w] = 0
		else:
			b_owes[w] += b_owes[e]
			e_owes[w] -= b_owes[e]
			b_owes[e] = 0

	if (e_owes[w] > 0 and w_owes[b] > 0):
		if(e_owes[w] >= w_owes[b]):
			e_owes[b] += w_owes[b]
			e_owes[w] -= w_owes[b]
			w_owes[b] = 0
		else:
			e_owes[b] += e_owes[w]
			w_owes[b] -= e_owes[w]
			e_owes[w] = 0

	if (e_owes[b] > 0 and b_owes[w] > 0):
		if(e_owes[b] >= b_owes[w]):
			e_owes[w] += b_owes[w]
			e_owes[b] -= b_owes[w]
			b_owes[w] = 0
		else:
			e_owes[w] += e_owes[b]
			b_owes[w] -= e_owes[b]
			e_owes[b] = 0

	# round all values to two decimal places
	w_owes[b] = round(w_owes[b], 2)
	w_owes[e] = round(w_owes[e], 2)
	b_owes[w] = round(b_owes[w], 2)
	b_owes[e] = round(b_owes[e], 2)
	e_owes[w] = round(e_owes[w], 2)
	e_owes[b] = round(e_owes[b], 2)
	
	# update users table of DB with updated debts
	w_doc["owes"] = w_owes
	b_doc["owes"] = b_owes
	e_doc["owes"] = e_owes
	users.save(w_doc)
	users.save(b_doc)
	users.save(e_doc)
	
	# send new balance to all members of Unger
	response += generateBalance(w_owes,b_owes,e_owes)
	client.sms.messages.create(to=w_number, from_=twilio_number, body=response)
	client.sms.messages.create(to=b_number, from_=twilio_number, body=response)
	client.sms.messages.create(to=e_number, from_=twilio_number, body=response)
	
	return ""
	
if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)