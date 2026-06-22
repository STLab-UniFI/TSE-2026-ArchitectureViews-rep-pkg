import os
import ast
import pandas as pd

import smtplib, ssl, time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SURVEY_LINK = "ANONYMIZED"


def iterate_address(doc_path, start_after=None):
    df = pd.read_csv(doc_path)
    start_index = 0
    
    if start_after is not None:
        start_index = df[df.iloc[:, 0] == start_after].index
        if not start_index.empty:
            start_index = start_index[0] + 1
        else:
            start_index = 0
    
    for index, row in df.iloc[start_index:].drop_duplicates().iterrows():
        yield row


def send_email_old(sender, psw_account, receiver, subject, html_body, plain_body):

    message = generate_message(sender, receiver, subject, html_body, plain_body)
    
    # Crea una connessione sicura con il server e invia l'email
    context = ssl.create_default_context()
    with smtplib.SMTP(ANONYMIZED) as server:
        server.starttls(context=context)
        server.login(sender, psw_account)
        server.sendmail(sender, receiver, message.as_string())
        print("email sent to:", receiver)



def generate_message(sender, receiver, subject, html_body, plain_body):
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = "Software Technologies Lab " + sender
    message["To"] = receiver

    text_part = MIMEText(plain_body, "plain")
    html_part = MIMEText(html_body, "html")

    message.attach(text_part)
    #message.attach(html_part)

    return message

def create_html_links(items):
    html_string = ', '.join([f'<a href="https://github.com/{item}">{item}</a>' for item in items])
    return html_string


def generate_html_body(repo_list):
    repos = create_html_links(repo_list)
    survey = f'<a href="{SURVEY_LINK}">Survey Link</a>'
    body = """\
    <html>
    <body>
    <pre style="font-family: Helvetica, sans-serif; font-size: 12px">
Dear Open Source Software Contributor,<br />

I am Leonardo Scommegna, a Software Engineering researcher at the University of Florence. <br /> 
Together with colleagues from the University of Florence and Vrije Universiteit Amsterdam, we are conducting a 5-minute survey to understand what makes a good architectural view in open source projects. <br />
We are contacting you because you have contributed to the following GitHub repositories in the past year: """ + str(repos) + """ <br />
We kindly ask you to participate in our survey. By doing so, you will have the opportunity to contribute to promising research in OSS development and help improve the tools and practices used by OSS developers worldwide. 

You can find the survey at the following link: """+ survey + """
Thank you for your time and contribution.

Best regards,
Leonardo

---
Leonardo Scommegna | Assistant Professor | University of Florence, Italy | <a href="https://leonardoscommegna.github.io/">leonardoscommegna.github.io</a><br />
Co-investigators:
Roberto Verdecchia (University of Florence)
Ivano Malavolta (Vrije Universiteit Amsterdam)
Patricia Lago (Vrije Universiteit Amsterdam)
Enrico Vicario (University of Florence)
    </body>
    </html>
    """
    return body

#def create_plain_links(items):
#    plain_string = ', '.join([f'{item} (https://github.com/{item})' for item in items])
#    return plain_string

def create_plain_links(items):
    plain_string = '\n'.join([f'- {item} (https://github.com/{item})' for item in items])
    return plain_string

def generate_plain_text_body(repo_list):
    repos = create_plain_links(repo_list)
    body = """\
Dear Open Source Software Contributor,

I am Leonardo Scommegna, a Software Engineering researcher at the University of Florence. 
Together with colleagues from the University of Florence and Vrije Universiteit Amsterdam, we are conducting a 5-minute survey to understand what makes a good architectural view in open source projects.

We are contacting you because you have contributed to the following GitHub repositories in the past year: 
""" + str(repos) + """

We kindly ask you to participate in our survey. By doing so, you will have the opportunity to contribute to promising research in OSS development and help improve the tools and practices used by OSS developers worldwide.

You can find the survey at the following link: """+ SURVEY_LINK + """
Thank you for your time and contribution.

Best regards,
Leonardo

---
Leonardo Scommegna | University of Florence, Italy | https://leonardoscommegna.github.io/

Co-investigators:
Roberto Verdecchia | University of Florence
Ivano Malavolta | Vrije Universiteit Amsterdam
Patricia Lago | Vrije Universiteit Amsterdam
Enrico Vicario | University of Florence
    """
    return body


def retrieve_credentials(credential_path):
    df = pd.read_csv(credential_path)
    return df['addr'].iloc[0], df['code'].iloc[0]

def generate_message_full(sender, receiver, subject, repos):
    html_body = generate_html_body(repos)
    plain_body = generate_plain_text_body(repos)
    return generate_message(sender, receiver, subject, html_body, plain_body)

def send_email(server, sender, receiver, subject, html_body, plain_body):
    message = generate_message(sender, receiver, subject, html_body, plain_body)
    server.sendmail(sender, receiver, message.as_string())
    print("Email sent to:", receiver)
    
def get_plain_text(message):
    for part in message.walk():
        if part.get_content_type() == "text/plain":  
            return part.get_payload(decode=True).decode(part.get_content_charset())

workdir = './'
addressdir="./addresses.csv"
credentials_path = 'ANONYMIZED'
subject = 'Invitation to Participate in OSS Survey'
sender_mail, psw = retrieve_credentials(credentials_path)

restart_from = None
if restart_from is None:
    mail_sent = pd.DataFrame(columns=['Email', 'Text' ])
    mail_sent.to_csv(os.path.join(workdir, 'mails-sent.csv'), index=False)

email_count = 0
email_index = 0
max_emails = 100

context = ssl.create_default_context()
with smtplib.SMTP(ANONYMIZED) as server:
    server.starttls(context=context)
    server.login(sender_mail, psw)

    for row in iterate_address(addressdir, restart_from):
        if email_count >= max_emails:
            print("Mail limit exceeded for today.")
            break
        email_index += 1
        receiver_address = row['Email']
        repos = ast.literal_eval(row['Repository'])
        #repos = ", ".join(repos.split(",")[:9]).replace('[', '').replace(']', '')
        message = generate_message_full(sender_mail, receiver_address, subject, repos)
        try:
            #server.sendmail(sender_mail, receiver_address, message.as_string())
            new_mail = pd.DataFrame({'Email': [receiver_address], 'Text': [get_plain_text(message)]})
            new_mail.to_csv(os.path.join(workdir, 'mails-sent.csv'), mode='a', header=False, index=False)
            email_count += 1
            #print("Email sent to:", receiver_address)
            print(f"Email sent to: {receiver_address}, email number {email_count}, index {email_index}.")
        except smtplib.SMTPRecipientsRefused:
                print(f"Recipient refused: {receiver_address}, email number {email_count}, index {email_index}.")
                new_mail = pd.DataFrame({'Email': [receiver_address], 'Text': ['REFUSED']})
                new_mail.to_csv(os.path.join(workdir, 'mails-sent.csv'), mode='a', header=False, index=False)

        time.sleep(0.5)
