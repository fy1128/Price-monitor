#!/usr/bin/env python3
# coding=utf-8
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr
from CONFIG import EMAIL_MIME_TYPE, MAIL_SMTP, MAIL_SMTP_NEED_AUTH, MAIL_SMTP_ACCOUNT, MAIL_SMTP_PASSWORD
from formater import strip_tags
import smtplib
import requests
import urllib, base64, json
import re
from os import path
import os
import logging

class Mail(object):

    def __init__(self, text, sender, receiver, subject, address):
        if MAIL_SMTP:
            self.server = self._get_mail_server(MAIL_SMTP)
            self.from_addr = MAIL_SMTP_ACCOUNT
            self.password = MAIL_SMTP_PASSWORD
    
        else:
            # mailbox setting
            local_dir = path.dirname(__file__)
            with open(os.path.join(local_dir, 'mailbox.txt'), 'r') as f:
                mail_setting = f.readlines()
            self.from_addr = mail_setting[0].strip()
            self.password = mail_setting[1].strip()
            smtp_server = mail_setting[2].strip()
            # server = smtplib.SMTP(self.smtp_server, 25)  # 25 normalï¼<8c>465 SSL
            self.server = smtplib.SMTP_SSL(smtp_server, 465)
            # server.starttls()  # SSL required
            
        if EMAIL_MIME_TYPE == 'html':
            text = text.replace('\n', '<br />')
        else:
            text = strip_tags(text)

        self.text = text
        self.sender = sender
        self.receiver = receiver
        self.subject = subject
        self.address = address
        self.to_addr = address
        # From above to below: mail content, sender nickname, receiver nickname, subject
        self.msg = MIMEText(self.text, EMAIL_MIME_TYPE, 'utf-8')
        self.msg['From'] = self._format_addr(self.sender + '<' + self.from_addr + '>')
        self.msg['To'] = self._format_addr(self.receiver + '<' + self.to_addr + '>')
        self.msg['Subject'] = Header(self.subject, 'utf-8').encode()

    # format the email address
    def _format_addr(self, s):
        name, addr = parseaddr(s)
        return formataddr((Header(name, 'utf-8').encode(), addr))

    def _get_mail_server(self, s):
        s = s.split(':')
        addr = ''.join(s[:-1])
        port = int(s[-1])
        if port == 465:
            return smtplib.SMTP_SSL(addr, port)
        else:
            return smtplib.SMTP(addr, port)

    def send(self):
        server = self.server
        server.set_debuglevel(1)
        if MAIL_SMTP_NEED_AUTH:
            server.login(self.from_addr, self.password)
        server.sendmail(self.from_addr, [self.to_addr], self.msg.as_string())
        logging.info('----This email\'s info: %s, %s, %s', self.text, self.receiver, self.to_addr)
        server.quit()

class Messager(object):
    def __init__(self, text, subject, endpoint, endpoint_data):
        msg = '{}\n{}'.format(subject, text)
        msg = str(base64.b64encode(urllib.parse.quote(msg).encode('utf-8')), 'utf-8')
        self.msg = msg

        data = Messager.is_json(endpoint_data)

        if data:
            data['msg'] = msg
            self.data = data

        self.url = endpoint.replace('{msg}', msg)
        
    def send(self):
        if hasattr(self, 'data'):
            method = 'post'
            requests.post(self.url, self.data, timeout = 30)
        else:
            method = 'get'
            requests.get(self.url, timeout = 30)
        logging.info('----This message\'s has been \'%s\' to: , %s', method, self.url)

    @staticmethod
    def is_json(str):
        if str is None:
            return False
        try:
            json_object = json.loads(str)
        except ValueError as e:
            return False
        return json_object


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    #send_email = Mail('test', 'wo', 'ni', 'test', '404013419@qq.com')
    #send_email.send()




