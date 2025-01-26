import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import paho.mqtt.client as mqtt

# Initialisation des données MQTT
mqtt_data = {
    "temperature": None, "humidity": None, "pm25": None, "pm10": None,
    "co": None, "no2": None, "co2": None
}

# Variables pour la gestion des alertes
alerts = []

# Callback pour réception des données MQTT
def on_message(client, userdata, msg):
    global mqtt_data, alerts
    try:
        mqtt_data[msg.topic.split("/")[-1]] = float(msg.payload.decode())
    except ValueError:
        pass  # Ignorer les erreurs de conversion

    # Vérifier les alertes (Exemple: seuil pour PM2.5)
    if mqtt_data["pm25"] is not None and mqtt_data["pm25"] > 50:
        alerts.append("Alerte: PM2.5 élevé ! (> 50 µg/m³)")
    if mqtt_data["temperature"] is not None and mqtt_data["temperature"] > 30:
        alerts.append("Alerte: Température élevée ! (> 30°C)")

# Connexion au broker MQTT
def start_mqtt():
    client = mqtt.Client()
    client.on_message = on_message
    client.connect("mqtt.eclipseprojects.io", 1883, 60)

    # S'abonner aux capteurs
    for topic in mqtt_data.keys():
        client.subscribe(f"data/{topic}")

    client.loop_forever()

# Lancer MQTT dans un thread séparé
import threading
threading.Thread(target=start_mqtt, daemon=True).start()

# Page des alertes
alertSystem_layout = html.Div([
    html.H1("⚠️ Système d'Alertes", style={'textAlign': 'center'}),
    
    html.Div(id='alert-messages', children='Aucune alerte pour le moment.'),
    
    html.Div([
        html.Button('Retour au Dashboard', id='back-to-dashboard', n_clicks=0),
    ], style={'textAlign': 'center'})
])

# Callback pour afficher les alertes
@app.callback(
    Output('alert-messages', 'children'),
    [Input('alert-messages', 'children')]
)
def update_alerts(_):
    if len(alerts) > 0:
        return html.Ul([html.Li(alert) for alert in alerts])
    return 'Aucune alerte pour le moment.'

