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
import json, datetime
import requests

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import ibm_db
import ibmiotf.application

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
        
def sendSlack(to, msg):
    try:
        headers = {
            'Content-type': 'application/json', 
            'Accept': 'text/plain',
            'Authorization': 'Bearer xoxb-83959766341-650053210930-Nf6jYeLVuACXwYKeRLPQMO57'
        }
        
        body = {}
        body['text'] = msg
        body['channel'] = to
        resp = requests.post('https://slack.com/api/chat.postMessage', 
                            headers=headers, 
                            data = json.dumps(body))

        if resp.status_code == 200:
            return True
    except Exception as e:
        print(e)