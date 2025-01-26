import paho.mqtt.client as mqtt

# Callback lorsque la connexion MQTT est établie
def on_connect(client, userdata, flags, rc, properties):  # Ajout de `properties`
    print("Connecté au broker MQTT avec le code de résultat "+str(rc))
    
    if rc == 0:
        print("Connexion réussie.")
        # Abonnement aux sujets que l'ESP32 publie
        client.subscribe("data/temperature")
        client.subscribe("data/humidity")
        client.subscribe("data/pm25")
        client.subscribe("data/pm10")
        client.subscribe("data/co")
        client.subscribe("data/no2")
        client.subscribe("data/co2")
    else:
        print(f"Échec de la connexion. Code de retour: {rc}")

# Callback lorsqu'un message est reçu
def on_message(client, userdata, msg):
    print(f"Message reçu sur le sujet {msg.topic}: {msg.payload.decode()}")

    # Traitement des données reçues
    data_mapping = {
        "data/temperature": "Température",
        "data/humidity": "Humidité",
        "data/pm25": "PM2.5",
        "data/pm10": "PM10",
        "data/co": "CO",
        "data/no2": "NO2",
        "data/co2": "CO2",
    }

    if msg.topic in data_mapping:
        print(f"{data_mapping[msg.topic]} : {msg.payload.decode()}")

# Créer un client MQTT
client = mqtt.Client(protocol=mqtt.MQTTv5)  # Utilisation de MQTT v5

# Lier les fonctions de callback
client.on_connect = on_connect
client.on_message = on_message

# Se connecter au broker MQTT
broker = "mqtt.eclipseprojects.io"  # Utilisation du même broker que dans l'ESP32
port = 1883
client.connect(broker, port, 60)

# Démarrer la boucle MQTT pour recevoir les messages
client.loop_forever()
