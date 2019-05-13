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
import uuid, json, datetime
import requests
import smtplib

import ibm_db
import ibmiotf.application

from bdp_notifier import BDPNotifier
import bdp_dbutil

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
            "type": "shared",
            "clean-session": True
        }
        client = ibmiotf.application.Client(options)
        client.connect()
        client.deviceEventCallback = hardwareCallback
        client.subscribeToDeviceEvents(deviceType=myDeviceType,deviceId="20WestSensor2")
    except ibmiotf.ConnectionException  as e:
        print(e)


def hardwareCallback(event):
    print("[hardwareCallback] msg from device [%s]: %s" % (event.device, json.dumps(event.data)))
    try:
        conn = bdp_dbutil.BDPDBConnection.getInstance().getDBConnection()

        # Generate timestamp and query hardware uid
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H.%M.%S")

        hardware = bdp_dbutil.getHardwareByDevice(conn, event.device)
        if not hardware:
            print("[hardwareCallback] Device {} not found.".format(event.device))
            return
        hardware_uid = hardware["HARDWARE_UID"]

        # Generate SQL string
        sql_string = "INSERT INTO " + bdp_dbutil.getTableName("BDP_RAW_EVENTS") + "(READING_TIME, READING, HARDWARE_UID) VALUES ('" 
        sql_string += str(timestamp) + "', '" + json.dumps(event.data) + "', '" + str(hardware_uid)  + "')"
        print("[hardwareCallback] Inserting to DB: {}".format(sql_string))
        
        # Save to DB
        stmt = ibm_db.exec_immediate(conn, sql_string)
        if ibm_db.num_rows(stmt) == 0:
            print("[hardwareCallback] Could not add the event to DB!")
            return
        
        # Process event
        BDPNotifier.handleEvents(conn, hardware)
        
    except Exception as e:
        print(e)
