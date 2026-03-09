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

def sendNotificationToUsers(endpoint, usergroups, action, userJSON):
    """ 
    Methods that notifies users of a specific action
    """
    try:
        resp = requests.post(
            endpoint + 'confirm', 
            headers = {
                'Content-type': 'application/json', 
                'Accept': 'text/plain'
                }, 
            data = json.dumps({
                "action": "CONFIRM", 
                "responder_action": action, 
                "group": usergroups, 
                "responder_info": userJSON["USER_CONTACT_1"]
            })
        )
        if resp.status_code == 200:
            print("[STATUS][bdp_util.sendNotificationToUsers] Action notification was sent: {}".format(action))
            return True
        else:
            print("[ERROR][bdp_util.sendNotificationToUsers] Notification was not sent. Status code: {}".format(resp.status_code))
    except Exception as e:
        print("[ERROR][bdp_util.sendNotificationToUsers] Something went wrong: {}".format(e))

    return False

def _buildEmailBody(to, subject, plain_body, html_body, sent_from):
    """ 
    Parses email body object

    :param to: Recipient email address
    :param subject: Email subject string
    :param plain_body: Message body without CSS styling
    :param html_body: Message body with CSS styling

    :return: Message object
    """
    message = MIMEMultipart('alternative')
    message['Subject'] = subject
    message['From'] = sent_from
    message['To'] = to

    plain_text = MIMEText(plain_body, 'plain')
    html_text = MIMEText(html_body, 'html')

    message.attach(plain_text)
    message.attach(html_text)

    return message

def sendEmails(emailList):
    """
    Sends multiple emails out to the emailing list

    :param emailList: List of email objects that containts email addresses and email message bodies
    """
    gmail_user = BDPProperty.getInstance().getValue('gmail_user')
    gmail_password = BDPProperty.getInstance().getValue('gmail_password')
    
    server = None
    try:  
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(gmail_user, gmail_password)
        for email in emailList:
            message = _buildEmailBody( 
                email.emailAddress, 
                email.subject,
                email.textBody, 
                email.htmlBody, 
                gmail_user
            )
            server.sendmail(gmail_user, email.emailAddress, message.as_string())
        print('[STATUS][bdp_util.sendEmails] Email notification was sent')
    except Exception as e:
        print('[ERROR][bdp_util.sendEmails] Email notification was not sent! Reason: {}'.format(e))
    finally:
        if (server != None):
            server.close()

def sendEmail(to, subject, plain_body, html_body):
    """
    Sends a single email out

    :param to: Recipient email address
    :param subject: Email subject string
    :param plain_body: Message body without CSS styling
    :param html_body: Message body with CSS styling
    """
    gmail_user = BDPProperty.getInstance().getValue('gmail_user')
    gmail_password = BDPProperty.getInstance().getValue('gmail_password')
    
    server = None
    try:  
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(gmail_user, gmail_password)

        message = _buildEmailBody(
            to, 
            subject, 
            plain_body, 
            html_body, 
            gmail_user
        )
        server.sendmail(gmail_user, to, message.as_string())
        print('[STATUS][bdp_util.sendEmail] Email notification was sent')

    except Exception as e:
        print('[ERROR][bdp_util.sendEmail] Email notification was not sent! Reason: {}'.format(e))

    finally:
        if (server != None):
            server.close()
        
def sendSlack(to, msg):
    """
    Sends a single Slack message out

    :param to: Recipient Slack ID
    :param msg: Message body

    :return: True is successful
    """
    try:
        resp = requests.post(
            'https://slack.com/api/chat.postMessage',
            headers = {
                'Content-type': 'application/json', 
                'Accept': 'text/plain',
                'Authorization': BDPProperty.getInstance().getValue('slack_auth')
                },
            data = json.dumps({
                'channel': to,
                'text': msg
                })
            )

        if resp.status_code == 200:
            print('[STATUS][bdp_util.sendSlack] Slack notification was sent')
            return True
        else:
            print('[ERROR][bdp_util.sendSlack] Response status code: {}'.format(resp.status_code))
    except Exception as e:
        print('[ERROR][bdp_util.sendSlack] Error occured: {}'.format(e))

def sendTririga(work_task_payload):
    """
    Creates Tririga work order

    :param work_task_payload: Tririga work task object

    :return: True is successful
    """
    try:    
        resp = requests.post(
            BDPProperty.getInstance().getValue('tririga_api'), 
            auth=HTTPBasicAuth(
                BDPProperty.getInstance().getValue('tririga_user'), 
                BDPProperty.getInstance().getValue('tririga_password')
                ), 
            headers = {'Content-type': 'application/json'},
            data=json.dumps(work_task_payload),
            # json=json.dumps(work_task_payload)
            )

        if resp.status_code == 200:
            print("[STATUS][bdp_util.sendTririga] Tritiga work order was created")
            return True
        else:
            print("[ERROR][bdp_util.sendTririga] Response status code: {}".format(resp.status_code))

    except Exception as e:
        print('[ERROR][bdp_util.sendTririga] Error occured: {}'.format(e))