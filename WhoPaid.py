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

# Our phone numbers
w_number = "+14254436511"
b_number = "+19256837230"
e_number = "+15615426296"

users_dict = {w_number:{'name':'w'},
			  b_number:{'name':'b'},
			  e_number:{'name':'e'}}
owes_dict = {}
	
def reduceCircularDebt(a,b,c):
	global owes_dict
	
	if (owes_dict[a][b] > 0 and owes_dict[b][c] > 0):
		if(owes_dict[a][b] >= owes_dict[b][c]):
			owes_dict[a][c] += owes_dict[b][c]
			owes_dict[a][b] -= owes_dict[b][c]
			owes_dict[b][c] = 0
		else:
			owes_dict[a][c] += owes_dict[a][b]
			owes_dict[b][c] -= owes_dict[a][b]
			owes_dict[a][b] = 0

def generateBalance():
	response = ""

	if(owes_dict['w']['b'] > 0):
		response += "w owes b: " + str(owes_dict['w']['b']) + "\n"
	if(owes_dict['w']['e'] > 0):
		response += "w owes e: " + str(owes_dict['w']['e']) + "\n"
	if(owes_dict['b']['w'] > 0):
		response += "b owes w: " + str(owes_dict['b']['w']) + "\n"
	if(owes_dict['b']['e'] > 0):	
		response += "b owes e: " + str(owes_dict['b']['e']) + "\n"
	if(owes_dict['e']['w'] > 0):
		response += "e owes w: " + str(owes_dict['e']['w']) + "\n"
	if(owes_dict['e']['b'] > 0):
		response += "e owes b: " + str(owes_dict['e']['b']) + "\n"

	return response

def processPayment(payer,payees,amount_charged):
	global owes_dict
	
	# Make payment to all relevant people
	for payee in payees:
		payer_owes_payee = owes_dict[payer][payee]
		payee_owes_payer = owes_dict[payee][payer]

		# Payer owes Payee case
		if (payer_owes_payee > 0):
			# Payer owes Payee more than he just paid, so deduct the amount paid from the total
			if (payer_owes_payee >= amount_charged):
				payer_owes_payee -= amount_charged
			# Payer owes Payee less than he just paid, so now Payee owes Payer some money
			else:
				payee_owes_payer = amount_charged - payer_owes_payee 
				payer_owes_payee = 0
		# Payee owes Payer case
		elif (payee_owes_payer >= 0):
			payee_owes_payer += amount_charged

		owes_dict[payer][payee] = payer_owes_payee
		owes_dict[payee][payer] = payee_owes_payer
	
	# reduce any circular debts
	# eg: E owes W x, W owes B y, so E should owe B x and W should owe B y - x,
	# although cased on whether x >= y
	reduceCircularDebt('w','b','e')
	reduceCircularDebt('w','e','b')
	reduceCircularDebt('b','w','e')
	reduceCircularDebt('b','e','w')
	reduceCircularDebt('e','w','b')
	reduceCircularDebt('e','b','w')

	# round all values to two decimal places
	owes_dict['w']['b'] = round(owes_dict['w']['b'], 2)
	owes_dict['w']['e'] = round(owes_dict['w']['e'], 2)
	owes_dict['b']['w'] = round(owes_dict['b']['w'], 2)
	owes_dict['b']['e'] = round(owes_dict['b']['e'], 2)
	owes_dict['e']['w'] = round(owes_dict['e']['w'], 2)
	owes_dict['e']['b'] = round(owes_dict['e']['b'], 2)

def unitTests():
	global owes_dict

	# basic payments
	owes_dict = {'w':{'b':0.00,'e':0.00},'b':{'w':0.00,'e':0.00},'e':{'w':0.00,'b':0.00}}
	processPayment('w',['b','e'],5)
	processPayment('w',['b','e'],5)
	processPayment('w',['b','e'],5)
	print generateBalance()

	# reduce circular debt
	owes_dict = {'w':{'b':0.00,'e':0.00},'b':{'w':0.00,'e':0.00},'e':{'w':0.00,'b':0.00}}
	processPayment('w',['b','e'],5)
	processPayment('e',['b'],5)
	print generateBalance()

@app.route('/', methods=['POST'])
def parseSMS():
	global owes_dict
	
	# Establish connection with Twilio
	client = TwilioRestClient(account, token)

	# Connect to MongoDB, and retrieve collections
	connection = Connection(MONGO_URL)
	db = connection.app7324197
	users = db.users
	payments = db.payments
	
	# Determine current debts
	w_doc = users.find_one({"username":'w'})
	b_doc = users.find_one({"username":'b'})
	e_doc = users.find_one({"username":'e'})
	owes_dict = {'w':w_doc["owes"],'b':b_doc["owes"],'e':e_doc["owes"]}

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
		response = generateBalance()
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
	if (amount <= 0):
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

	# retrieve info about user who submitted payment
	payer_dict = users_dict.get(from_number,None)
	if(payer_dict == None):
		response = "Not part of the land down Unger"
		client.sms.messages.create(to=from_number, from_=twilio_number, body=response)
		return ""

	# Register payment
	if(pay_all):
		payments.insert({"Amount":amount,"From":payer_dict["name"],"To":"All"})
		response = payer_dict["name"] + " paid " + str(amount) + "\n"
	else:
		payments.insert({"Amount":amount,"From":payer_dict["name"],"To":body_array[1]})
		response = payer_dict["name"] + " paid " + body_array[1] + " " + str(amount) + "\n"

	# Determine who is involved in the payment
	payees = []
	if (pay_all):
		payees.append("w")
		payees.append("b")
		payees.append("e")
	else:
		payees.append(body_array[1])

	payees.remove(payer_dict["name"])

	# Complete payment, resolve circular debt, and round
	processPayment(payer_dict["name"],payees,amount_charged)

	# update users table of DB with updated debts
	w_doc["owes"] = owes_dict['w']
	b_doc["owes"] = owes_dict['b']
	e_doc["owes"] = owes_dict['e']
	users.save(w_doc)
	users.save(b_doc)
	users.save(e_doc)

	# send new balance to all members of Unger
	response += generateBalance()
	client.sms.messages.create(to=w_number, from_=twilio_number, body=response)
	client.sms.messages.create(to=b_number, from_=twilio_number, body=response)
	client.sms.messages.create(to=e_number, from_=twilio_number, body=response)
	
	return ""
	
if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)