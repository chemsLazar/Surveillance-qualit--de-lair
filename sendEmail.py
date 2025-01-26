import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

last_email_time = 0  # Gérer l'intervalle d'envoi des emails

# Fonction pour envoyer des alertes par email avec un format structuré
def send_email(alerts):
    sender_email = "lazarchams@gmail.com"
    receiver_email = "lazarchams@gmail.com"
    password = "crme tvkc fafx lrcf"
    
    subject = "🚨 Alerte : Qualité de l'Air Dégradée"
    
    # Construire le corps du message en HTML
    body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2 style="color: red;">🚨 Alerte de Qualité de l'Air 🚨</h2>
            <p>Bonjour,</p>
            <p>Les capteurs ont détecté des valeurs critiques dans la qualité de l'air :</p>
            <ul>
                {''.join(f"<li><b>{alert}</b></li>" for alert in alerts)}
            </ul>
            <p>Veuillez prendre les mesures nécessaires.</p>
            <hr>
            <p style="font-size: 12px; color: #888;">Ceci est un message automatique. Ne répondez pas à cet email.</p>
        </body>
    </html>
    """
    
    # Création du message
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "html"))  # Envoi en HTML

    # Envoi de l'email via le serveur SMTP de Gmail
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
            print("✅ Email envoyé avec succès!")
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi de l'email: {e}")

