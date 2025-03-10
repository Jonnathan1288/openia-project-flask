import smtplib
from email.message import EmailMessage

from models.email import Email


def send_Email( email: Email ) -> bool:
    remitente = 'estebanbacuilima@gmail.com'
    to = email.get_to()
    mensaje = email.get_mensaje()
    subject = email.get_subject()

    email = EmailMessage()
    email["From"] = remitente
    email["To"] = to
    email["Subject"] = subject
    email.set_content(mensaje)

    smtp = smtplib.SMTP_SSL('smtp.gmail.com')
    smtp.login(remitente, "dbtr eclt gysb glnd")
    smtp.sendmail(remitente, to, 
                email.as_string())
    smtp.quit()

    return True     