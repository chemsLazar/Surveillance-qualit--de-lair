import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Fonction pour envoyer des alertes par email
def send_email(alerts):
    sender_email = "lazarchams@gmail.com"
    receiver_email = "lazarchams@gmail.com"
    password = "crme tvkc fafx lrcf"
    subject = "Alertes Qualité de l'Air"
    body = "\n".join(alerts)

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
            print("Email envoyé avec succès!")
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email: {e}")
