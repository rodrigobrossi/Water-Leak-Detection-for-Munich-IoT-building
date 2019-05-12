#############################################################
# IBM Confidential
# OCO Source Materials
#
#  (C) Copyright IBM Corp. 2019
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has
# been deposited with the U.S. Copyright Office.
#############################################################
import uuid, json
import requests
import smtplib
import ibmiotf.application
from bdp_notifier import BDPNotifier


def randomString(string_length=10):
    """Returns a random string of length string_length."""
    random = str(uuid.uuid4()) # Convert UUID format to a Python string.
    random = random.upper() # Make all characters uppercase.
    random = random.replace("-","") # Remove the UUID '-'.
    return random[0:string_length] # Return the random string.

def sendNotificationToUsers(endpoint, usergroups, action, userJSON):
    print("sendNotificationToUsers: " + action)
    print(userJSON)
    print(usergroups)
    try:
        url = endpoint + 'confirm'
            
        print(url)
        requestbody = {"action": "CONFIRM", "responder_action": action, "group": usergroups, "responder_info": userJSON["USER_CONTACT_1"]}
        print(requestbody)
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        resp = requests.post(url, headers=headers, data = json.dumps(requestbody))
    
        print(resp.status_code)
        print(resp.text)
        if resp.status_code == 200:
            return True
    except Exception as e:
        print(e)

    return False

def sendEmail(to):
    print("sendEmail: " + to)
    gmail_user = 'water.intrusion.munich@gmail.com'
    gmail_password = 'watsoniot'
    
    sent_from = gmail_user  
    to = ['cyjiang@us.ibm.com']
    subject = 'Subject: Urgent Message from Building Damage Protection System'
    body = 'Body: Urgent Message from Building Damage Protection System'
    
    message = 'Subject: {}\n\n{}'.format(subject, body)
    
    try:  
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(gmail_user, gmail_password)
        server.sendmail(sent_from, to, message)
        server.close()
    
        print('Email sent!')
    except Exception as e:
        print(e)  
        print('Something went wrong...')
        

def startIOT():
    iotSubscribe()
    
def iotSubscribe():
    try:
        myDeviceType="waterLeakDetector"
        options = {
            "org": "h9eyui",
            "id": "orgfx53ykk",
            "auth-method": "apikey",
            "auth-key": "a-h9eyui-orgfx53ykk",
            "auth-token": "rGXJy+2xk1FbSzCR&-",
            "clean-session": True
        }
        client = ibmiotf.application.Client(options)
        client.connect()
        client.deviceEventCallback = BDPNotifier.hardwareCallback
        client.subscribeToDeviceEvents(deviceType=myDeviceType,deviceId="20WestSensor2")
    except ibmiotf.ConnectionException  as e:
        print(e)
        
def myEventCallback(event):
    str = "%s event '%s' received from device [%s]: %s"
    print(str % (event.format, event.event, event.device, json.dumps(event.data)))
    for attr in dir(event): 
        print(attr)
        print(getattr(event, attr)) 