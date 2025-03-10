from email.message import EmailMessage
import smtplib

from models.email import Email

def send_Email( email: Email ) -> bool:
    remitente = 'estebanbacuilima@gmail.com'
    destinatario = 'javiertimbe100@gmail.com'
    mensaje = 'Hola Pildoras'

    email = EmailMessage()
    email["From"] = remitente
    email["To"] = destinatario
    email["Subject"] = 'Email Test'
    email.set_content(mensaje)

    smtp = smtplib.SMTP_SSL('smtp.gmail.com')
    smtp.login(remitente, "dbtr eclt gysb glnd")
    smtp.sendmail(remitente, destinatario, 
                email.as_string())
    smtp.quit()

    return True     