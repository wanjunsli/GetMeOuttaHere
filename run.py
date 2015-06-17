from flask import Flask, request, redirect, Response 
import twilio.twiml
from twilio.rest import TwilioRestClient
import time 
from datetime import datetime
import threading 
import logging

app = Flask(__name__)

escapesToBeMade = {}
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route("/", methods=['GET', 'POST'])
def runApp():
    fromNumber = str(request.values.get('From', None))
    fromBody = str(request.values.get('Body', None))

    if fromBody is None: 
    	message = "Incorrect request. Please retry with format: [HH:MM] [AM/PM] [EXCUSE MESSAGE]"
    else:
    	# preprocessing
        timeRequested = str(fromBody.split()[0])
        endTime = str(fromBody.split()[0])
        dayOrNight = str(fromBody.split()[1]).upper()
        excuse = " ".join(fromBody.split()[2:])

        checkTime = endTime.split(":")
        if int(checkTime[0]) < 1 or int(checkTime[0]) > 12 or int(checkTime[1]) < 0 or int(checkTime[1]) > 59:
            resp = twilio.twiml.Response()
            message = "Incorrect request. Please retry with format: [HH:MM] [AM/PM] [EXCUSE MESSAGE]"
            resp.message(message)
            return str(resp)

        if dayOrNight is None or (dayOrNight != "AM" and dayOrNight != "PM"):
            resp = twilio.twiml.Response()
            message = "Incorrect request. Please retry with format: [HH:MM] [AM/PM] [EXCUSE MESSAGE]"
            resp.message(message)
            return str(resp)


        if dayOrNight == "PM":
            hour = int(endTime.split(":")[0])
            if hour != 12: 
                hour += 12
            endTime = str(hour) + ":" + endTime.split(":")[1] + ":00"
        else:
            if int(endTime.split(":")[0]) == 12: 
                endTime = "00:" + endTime.split(":")[1] + ":00"
            else:
                endTime += ":00"

    	escapesToBeMade[fromNumber] = [endTime, dayOrNight, excuse]

    	startTime = time.strftime("%H:%M:%S")

        fmt = "%H:%M:%S"
        timeDifferenceInSecs = (datetime.strptime(endTime, fmt) - datetime.strptime(startTime, fmt)).total_seconds()
        
        timer = threading.Timer(timeDifferenceInSecs, makeEscape, [fromNumber])
        timer.start()
        
        message = "Your request has been received. Your escape route will be delivered at %s %s" % (timeRequested, dayOrNight.upper())
        logger.info("Request made by : %s\t Message: %s\t Time: %s" % (fromNumber, excuse, timeRequested))

    resp = twilio.twiml.Response()
    resp.message(message)

    return str(resp)
 
@app.route("/makeEscapeCall", methods=['GET', 'POST'])
def makeEscapeCall():
    number = str(request.values.get('To', None))
    getUserInformation = escapesToBeMade[number]
    message = getUserInformation[2]

    logger.info("Calling Number: %s\t with Message: %s " % (number, message))

    resp = twilio.twiml.Response()
    resp.say(message, voice='alice')

    return Response(str(resp), mimetype='text/xml')

def makeEscape(toNumber):
    account_sid = ""
    auth_token = ""
    client = TwilioRestClient(account_sid, auth_token)

    fromNumber = ""

    call = client.calls.create(to=toNumber, from_=fromNumber, url="/makeEscapeCall")

if __name__ == "__main__":
    app.run(debug=True)
