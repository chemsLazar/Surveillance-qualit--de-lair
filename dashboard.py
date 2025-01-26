import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import threading
import paho.mqtt.client as mqtt
import time
import sendEmail

# Initialisation des données MQTT
mqtt_data = {
    "temperature": None, "humidity": None, "pm25": None, "pm10": None,
    "co": None, "no2": None, "co2": None
}

# Variables pour stocker les valeurs précédentes pour les graphiques en ligne
pm25_values = []
pm10_values = []
co_values = []
co2_values = []
no2_values = []
humidity_values = []
temperature_values = []

# Seuils critiques pour chaque capteur
CRITICAL_THRESHOLDS = {
    "temperature": {"min": 0, "max": 40},
    "humidity": {"min": 20, "max": 80}, 
    "pm25": {"min": 0, "max": 50},   
    "pm10": {"min": 0, "max": 50},
    "co": {"min": 0, "max": 10},
    "co2": {"min": 350, "max": 1000},
    "no2": {"min": 0, "max": 200},
}

alerts = []

# Initialisation de last_email_time
last_email_time = 0  # Ajout de cette ligne pour initialiser last_email_time

# Callback pour réception des données MQTT
def on_message(client, userdata, msg):
    global mqtt_data
    try:
        mqtt_data[msg.topic.split("/")[-1]] = float(msg.payload.decode())
    except ValueError:
        pass  

# Fonction de connexion au broker MQTT
def start_mqtt():
    client = mqtt.Client()
    client.on_message = on_message
    client.connect("mqtt.eclipseprojects.io", 1883, 60)

    for topic in mqtt_data.keys():
        client.subscribe(f"data/{topic}")

    client.loop_forever()

# Lancer MQTT dans un thread séparé
threading.Thread(target=start_mqtt, daemon=True).start()

# DASHBOARD DASH
app = dash.Dash(__name__)
app.title = "Surveillance Qualité de l'Air"

# Importer la fonction pour envoyer des emails
from sendEmail import send_email

# Fonction pour vérifier les anomalies
def check_anomalies():
    global mqtt_data, alerts, last_email_time
    alerts = []
    current_time = time.time()

    for sensor, thresholds in CRITICAL_THRESHOLDS.items():
        value = mqtt_data.get(sensor)
        if value is not None:
            if value < thresholds["min"]:
                alerts.append(f"⚠️ {sensor} trop bas (Seuil: {thresholds['min']})")
            elif value > thresholds["max"]:
                alerts.append(f"⚠️ {sensor} trop élevé (Seuil: {thresholds['max']})")

            # Vérification des alertes critiques
            if sensor == "pm25" and value > 80:
                alerts.append(f"🚨 {sensor} CRITIQUE ! (Valeur: {value}, Seuil: 80)")
            if sensor == "temperature" and value > 40:
                alerts.append(f"🚨 {sensor} CRITIQUE ! (Valeur: {value}, Seuil: 40)")

    # Vérifier si des alertes existent et si 3 minutes se sont écoulées depuis le dernier email
    if alerts and (current_time - last_email_time > 180):  # 180 secondes = 3 minutes
        send_email(alerts)
        last_email_time = current_time  # Mettre à jour le dernier envoi


# Mise à jour des graphiques en temps réel
@app.callback(
    [
        Output('graph-pm', 'figure'),
        Output('graph-co2', 'figure'),
        Output('graph-humidity', 'figure'),
        Output('graph-temperature', 'figure'),
        Output('alerts-container', 'children')
    ],
    [Input('interval-component', 'n_intervals')]
)
def update_graphs(n_intervals):
    global mqtt_data, pm25_values, pm10_values, co_values, co2_values, no2_values, humidity_values, temperature_values, last_email_time

    # Vérification des anomalies et envoi d'email si nécessaire
    check_anomalies()

    def update_line_chart(values, new_value):
        """ Ajouter la nouvelle valeur et conserver l'historique. """
        if new_value is not None:
            values.append(new_value)
            if len(values) > 20:
                values.pop(0)
        return values

    def create_bar_figure(title, pm25, pm10):
        """ Crée un graphique en barres pour PM2.5 et PM10 """
        figure = go.Figure()
        figure.add_trace(go.Bar(x=['PM2.5', 'PM10'], y=[pm25, pm10], marker={'color': ['#1f77b4', '#ff7f0e']}))
        figure.update_layout(title=title)
        return figure

    def create_line_figure(title, values, color, name):
        """ Crée un graphique en ligne """
        figure = go.Figure()
        figure.add_trace(go.Scatter(
            x=list(range(len(values))),
            y=values,
            mode='lines+markers',
            name=name,
            line={'color': color}
        ))
        figure.update_layout(title=title, showlegend=True)
        return figure

    def create_gauge_figure(title, value, min_value, max_value, color):
        """ Crée un graphique en jauge (gauge chart) """
        figure = go.Figure()
        figure.add_trace(go.Indicator(
            mode="gauge+number",
            value=value if value is not None else 0,
            title={'text': title},
            gauge={'axis': {'range': [min_value, max_value]}, 'bar': {'color': color}}
        ))
        figure.update_layout(margin={'t': 50, 'b': 50, 'l': 50, 'r': 50})
        return figure

    # Mettre à jour les valeurs pour les graphiques en ligne
    pm25_values = update_line_chart(pm25_values, mqtt_data.get("pm25"))
    pm10_values = update_line_chart(pm10_values, mqtt_data.get("pm10"))
    co_values = update_line_chart(co_values, mqtt_data.get("co"))
    co2_values = update_line_chart(co2_values, mqtt_data.get("co2"))
    no2_values = update_line_chart(no2_values, mqtt_data.get("no2"))
    humidity_values = update_line_chart(humidity_values, mqtt_data.get("humidity"))
    temperature_values = update_line_chart(temperature_values, mqtt_data.get("temperature"))

    # Graphique PM2.5 et PM10 (Bar Chart)
    pm_figure = create_bar_figure("PM2.5 et PM10 (µg/m³)", mqtt_data["pm25"], mqtt_data["pm10"])

    # Graphique CO, CO2, NO2 (Line Chart)
    co_figure = create_line_figure("CO, CO2, NO2 (ppm)", co_values, '#d62728', 'CO')
    co_figure.add_trace(go.Scatter(x=list(range(len(co2_values))), y=co2_values, mode='lines+markers', name='CO2', line={'color': '#2ca02c'}))
    co_figure.add_trace(go.Scatter(x=list(range(len(no2_values))), y=no2_values, mode='lines+markers', name='NO2', line={'color': '#9467bd'}))

    # Graphique Humidité (Line Chart)
    humidity_figure = go.Figure()
    humidity_figure.add_trace(go.Scatter(
        x=list(range(len(humidity_values))),
        y=humidity_values,
        mode='lines+markers',
        name="Humidité",
        line={'color': '#17becf'}
    ))
    humidity_figure.update_layout(title="Humidité (%)")

    # Graphique Température (Gauge Chart)
    temperature_figure = create_gauge_figure("Température (°C)", mqtt_data["temperature"], -10, 50, '#ff7f0e')

    # Mise à jour des alertes : afficher seulement les alertes détectées
    alert_elements = []
    if alerts:
        for alert in alerts:
            # Pour les alertes critiques ou élevées, appliquer le fond uniquement au texte
            if "trop élevé" in alert or "CRITIQUE" in alert:
                alert_elements.append(
                    html.Div(
                        children=[
                            html.Span(
                                alert, 
                                style={
                                    'color': 'white', 
                                    'fontWeight': 'bold', 
                                    'backgroundColor': '#FF6347',  # Rouge orangé
                                    'padding': '5px', 
                                    'borderRadius': '5px'
                                }
                            )
                        ],
                        style={'marginBottom': '10px'}  # Espace de 10px entre les alertes
                    )
                )
            else:
                # Autres alertes normales (par exemple "trop bas")
                alert_elements.append(
                    html.Div(
                        children=[
                            html.Span(
                                alert, 
                                style={
                                    'color': 'white', 
                                    'fontWeight': 'bold', 
                                    'backgroundColor': '#FFA500',  # Orange
                                    'padding': '5px', 
                                    'borderRadius': '5px'
                                }
                            )
                        ],
                        style={'marginBottom': '10px'}  # Espace de 10px entre les alertes
                    )
                )
    else:
        # Si aucune anomalie, mettre une alerte "Aucune anomalie détectée" en vert
        alert_elements.append(
            html.Div(
                children=[
                    html.Span(
                        "Aucune anomalie détectée.",
                        style={
                            'color': 'green', 
                            'fontWeight': 'bold', 
                            'backgroundColor': '#e0f7e0',  # Vert clair
                            'padding': '5px', 
                            'borderRadius': '5px'
                        }
                    )
                ],
                style={'marginBottom': '10px'}  # Espace de 10px entre les alertes
            )
        )



    return pm_figure, co_figure, humidity_figure, temperature_figure, alert_elements

app.layout = html.Div([
    html.H1("📊 Dashboard - Surveillance Qualité de l'Air", style={'textAlign': 'center'}),

    html.Div("Suivi en temps réel de la qualité de l'air à partir des capteurs IoT.", style={'textAlign': 'center', 'fontSize': '20px', 'marginBottom': '20px', 'color': '#555'}),

    dcc.Interval(id='interval-component', interval=2000, n_intervals=0),

    html.Div(id='alerts-container',
             style={'color': 'green', 'fontWeight': 'bold', 'marginTop': '20px', 'textAlign': 'center'}),  # Centrer le texte

    # Graphes pour chaque capteur
    html.Div([
        dcc.Graph(id='graph-pm'),
        dcc.Graph(id='graph-co2'),
        dcc.Graph(id='graph-humidity'),
        dcc.Graph(id='graph-temperature')
    ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(2, 1fr)', 'gap': '20px'})
])

if __name__ == '__main__':
    app.run_server(debug=True)
