import streamlit as st
import datetime
from geopy.geocoders import Nominatim
import requests
import pydeck as pdk
import pandas as pd

st.title("TaxiFareModel Front")

# Inputs
date = st.date_input("When is your ride coming?")
time = st.time_input("At what time is your ride coming?")
pickup = st.text_input("Pickup address", "Manhattan, NY")
dropoff = st.text_input("Drop-off address", "New York, NY")
passenger = st.number_input("Number of passengers", min_value=1, step=1, format="%d")

# Bouton Predict
if st.button("Predict"):

    if not pickup or not dropoff:
        st.error("Please provide pickup & dropoff.")
    else:
        # Géocodage
        geolocator = Nominatim(user_agent="streamlit_app")
        try:
            pickup_location = geolocator.geocode(pickup, timeout=5)
            dropoff_location = geolocator.geocode(dropoff, timeout=5)
        except Exception as e:
            st.error(f"Geocoding error: {e}")
            st.stop()

        if not pickup_location or not dropoff_location:
            st.error("Impossible de géocoder les adresses.")
            st.stop()

        # Carte pydeck
        df = pd.DataFrame({
            "lat": [pickup_location.latitude, dropoff_location.latitude],
            "lon": [pickup_location.longitude, dropoff_location.longitude],
            "color": [[255,0,0], [0,0,255]]
        })
        point_layer = pdk.Layer(
            "ScatterplotLayer",
            data=df,
            get_position='[lon, lat]',
            get_color='color',
            get_radius=100,
        )
        line_layer = pdk.Layer(
            "LineLayer",
            data=pd.DataFrame({
                "from_lon":[pickup_location.longitude],
                "from_lat":[pickup_location.latitude],
                "to_lon":[dropoff_location.longitude],
                "to_lat":[dropoff_location.latitude]
            }),
            get_source_position='[from_lon, from_lat]',
            get_target_position='[to_lon, to_lat]',
            get_color='[0, 255, 0]',
            get_width=4,
        )
        midpoint_lat = (pickup_location.latitude + dropoff_location.latitude)/2
        midpoint_lon = (pickup_location.longitude + dropoff_location.longitude)/2
        view_state = pdk.ViewState(latitude=midpoint_lat, longitude=midpoint_lon, zoom=11)
        st.pydeck_chart(pdk.Deck(layers=[point_layer, line_layer], initial_view_state=view_state))

        # Création des params pour l'API
        pickup_datetime_str = datetime.datetime.combine(date, time).strftime("%Y-%m-%d %H:%M:%S")
        params = {
            "pickup_datetime": pickup_datetime_str,
            "pickup_latitude": pickup_location.latitude,
            "pickup_longitude": pickup_location.longitude,
            "dropoff_latitude": dropoff_location.latitude,
            "dropoff_longitude": dropoff_location.longitude,
            "passenger_count": passenger
        }

        # Appel API
        url = 'https://taxifare-262006090037.europe-west1.run.app/predict'
        try:
            response = requests.get(url, params=params, timeout=180)
            if response.status_code == 200:
                prediction = response.json().get("fare")
                if prediction is not None:
                    st.success(f"Estimated fare: {prediction:.2f} $")
                else:
                    st.error("Impossible de lire la prédiction dans le JSON.")
            else:
                st.error(f"API Error: {response.status_code}")
        except Exception as e:
            st.error(f"API call error: {e}")
