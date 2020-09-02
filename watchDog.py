import time
import json
from obspy import UTCDateTime

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def sendAlert():
    mail_content = '''elab stopped!!'''
    #The mail addresses and password
    sender_address ='sandrovezzosi@gmail.com' #'sandro@geco-company.com'
    sender_pass = 'paciugO80'
    receiver_address = 'sandrovezzosi@gmail.com' #'sandro@geco-company.com'
    #Setup the MIME
    message = MIMEMultipart()
    message['From'] = sender_address
    message['To'] = receiver_address
    message['Subject'] = 'Braskem elab stopped'   #The subject line
    #The body and the attachments for the mail
    message.attach(MIMEText(mail_content, 'plain'))
    #Create SMTP session for sending the mail
    session = smtplib.SMTP('smtp.gmail.com', 587) #use gmail with port
    session.starttls() #enable security
    session.login(sender_address, sender_pass) #login with mail_id and password
    text = message.as_string()
    session.sendmail(sender_address, receiver_address, text)
    session.quit()
    print('Mail Sent')


def check(fileName,col,timeOut=600):
    try:
        with open(fileName, 'r') as fp:
            p = json.load(fp)
            log = {k: UTCDateTime.strptime(p[k],"%Y-%m-%d %H:%M:%S") for k in p}
            fp.close()
        return  log[col]<UTCDateTime.now()-timeOut
    except:
        return True

rrOld=False
rrOld1=False

while 1<2:
    tt=False
    tt1=False
    rr=check('lastRaw.json','lastRcv',180)
    if rr & (not rrOld):
       tt=True
    rrOld=rr

    rr1 = check('lastDet.json', 'lastElab',1200)
    if rr1 & (not rrOld1):
        tt1 = True
    rrOld1 = rr1

    if tt | tt1:
        sendAlert()

    print(UTCDateTime.now())
    time.sleep(60)
