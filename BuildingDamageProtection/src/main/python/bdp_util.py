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
from requests.auth import HTTPBasicAuth

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bdp_property import BDPProperty

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

def sendEmails(emailList):
    gmail_user = 'water.intrusion.munich@gmail.com'
    gmail_password = 'watsoniot'
    sent_from = gmail_user

    server = None

    try:  
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(gmail_user, gmail_password)
        for email in emailList:
            message = _buildMessage(email, sent_from)
            server.sendmail(sent_from, email.emailAddress, message.as_string())
            print('Email sent!')

    except Exception as e:
        print(e)  
        print('Something went wrong...')
    finally:
        if (server != None):
            server.close()

def _buildMessage(email, sent_from):
    message = MIMEMultipart('alternative')
    message['Subject'] = email.subject
    message['From'] = sent_from
    message['To'] = email.emailAddress

    plain_text = MIMEText(email.textBody, 'plain')
    html_text = MIMEText(email.htmlBody, 'html')

    message.attach(plain_text)
    message.attach(html_text)
    return message


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
    
    server = None
    try:  
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(gmail_user, gmail_password)
        server.sendmail(sent_from, to, message.as_string())
        print('Email sent!')
    except Exception as e:
        print(e)  
        print('Something went wrong...')
    finally:
        if (server != None):
            server.close()
        
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

def sendTririga(work_task_payload):
    try:    
        # print('-------------------------BDPProperty.getInstance().getValue()--------------------------')
        # print(BDPProperty.getInstance().getValue('tririga_api'))
        # print(BDPProperty.getInstance().getValue('tririga_user'))
        # print(BDPProperty.getInstance().getValue('tririga_password'))
        # print(work_task_payload)
        resp = requests.post(BDPProperty.getInstance().getValue('tririga_api'), 
                            auth=HTTPBasicAuth(BDPProperty.getInstance().getValue('tririga_user'), BDPProperty.getInstance().getValue('tririga_password')), 
                            data = work_task_payload)

        print(resp.status_code)
        if resp.status_code == 201:
            return True
    except Exception as e:
        print(e)