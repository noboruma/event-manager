import smtplib, ssl

class Context:
    def __init__(self, smtp_server, port, sender_email, sender_passwd=None):
        self.smtp_server = smtp_server
        self.port = int(port)
        self.sender_email = sender_email
        self.sender_passwd = sender_passwd

def send_email(context, receiver_email, message):
    with smtplib.SMTP(context.smtp_server, context.port) as server:
        if context.sender_passwd is not None:
            server.login(context.sender_email, context.sender_passwd)
        server.sendmail(context.sender_email, receiver_email, message)

def send_notification(context, registered_email, event_name):
    message = f"""\
Subject: New event registration
To: {context.sender_email}
From: {context.sender_email}

{registered_email} has registered for {event_name}."""
    send_email(context, context.sender_email, message)

def send_calendar_invite(context, receiver_email, event):
    message = f"""\
Subject: Invite for {event.name} event
To: {receiver_email}
From: {context.sender_email}

Please come at: {event.location} between {event.start_timestamp} and {event.end_timestamp}."""
    send_email(context, receiver_email, message)
