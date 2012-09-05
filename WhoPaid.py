from twilio.rest import TwilioRestClient

account = "AC74068c46306d722c23fc68291b67071a"
token = "da09cf1ce50760e7ef4405d9c8334239"
client = TwilioRestClient(account, token)

for message in client.sms.messages.list():
    print message.body

message = client.sms.messages.create(to="+14254436511", from_="+14259678372",
                                     body="Hello there!")
