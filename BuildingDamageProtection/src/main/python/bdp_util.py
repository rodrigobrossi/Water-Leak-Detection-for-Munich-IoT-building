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
import pandas as pd
import matplotlib.pyplot as plt

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import ibm_db
import ibmiotf.application

from bdp_incident import BDPIncident
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

def sendEmail(to, subject, plain_body, html_body):
    gmail_user = 'water.intrusion.munich@gmail.com'
    gmail_password = 'watsoniot'
    sent_from = gmail_user  
    
    message = MIMEMultipart('alternative')
    message['Subject'] = subject
    message['From'] = sent_from
    message['To'] = to

    plain_text = MIMEText(plain_body, 'plain')
    html_text = MIMEText(html_body, 'html')

    message.attach(plain_text)
    message.attach(html_text)
    
    try:  
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(gmail_user, gmail_password)
        server.sendmail(sent_from, to, message.as_string())
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
        client.subscribeToDeviceEvents(deviceType=myDeviceType,deviceId="20WestSensor1")
    except ibmiotf.ConnectionException  as e:
        print(e)


def hardwareCallback(event):
    try:
        conn = bdp_dbutil.BDPDBConnection.getInstance().getDBConnection()

        # Generate timestamp and query hardware uid
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H.%M.%S")

        hardware = bdp_dbutil.getHardwareByDevice(event.device)
        if not hardware:
            print("[hardwareCallback] Device {} not found.".format(event.device))
            return
        hardware_uid = hardware["HARDWARE_UID"]

        # Generate SQL string
        sql_string = "INSERT INTO " + bdp_dbutil.getTableName("BDP_RAW_EVENTS") + "(READING_TIME, READING, HARDWARE_UID) VALUES ('" 
        sql_string += str(timestamp) + "', '" + json.dumps(event.data) + "', '" + str(hardware_uid)  + "')"
        
        # Save to DB
        stmt = ibm_db.exec_immediate(conn, sql_string)
        if ibm_db.num_rows(stmt) == 0:
            print("[hardwareCallback] Could not add the event to DB!")
            return
        
        # Process event
        BDPIncident.handleRawEvents(hardware)
        
    except Exception as e:
        print(e)

def createHumidityTable(hardware_uid, datapoint_amount):
    table = pd.DataFrame(bdp_dbutil.getRawEventsByHardwareUID(hardware_uid, 480))

    # Get important values
    table['HUMIDITY'] = None
    for i in range(table.shape[0]):
        hardware_json = json.loads(table.READING.iloc[i])
        table.at[i, 'HUMIDITY']  = hardware_json['humidity']
    return table

def createPlot(hardware_uid):
    table = createHumidityTable(hardware_uid, 480)
    figure, ax = plt.subplots(1,1)
    ax.set_facecolor('#182935')
    ax.xaxis.set_label_text('')
    figure = table.plot(x='READING_TIME', y='HUMIDITY', ax=ax, figsize=(12,4), legend=None, linewidth=4).get_figure()
    #TODO Fix path
    figure.savefig('src/main/python/static/img/plot_' + str(hardware_uid) +'.png', bbox_inches='tight')
