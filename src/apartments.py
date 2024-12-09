import streamlit as st
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from llm import geocode_address  # Importing the geocoding function
from dotenv import load_dotenv
import os
from email_tool import send_email, validate_email
load_dotenv()

def load_data():
    path = './data/apartments_for_rent_classified_10K.csv'
    data = pd.read_csv(path, delimiter=';', encoding='ISO-8859-1')
    data = data.dropna(subset=['latitude', 'longitude', 'address'])
    data = data[data['address'].str.strip() != '']
    return data

@st.cache_data  # Cache the results of this function
def get_nearest_apartments(df, lat, long, num_neighbors):
    nn = NearestNeighbors(n_neighbors=num_neighbors, algorithm='ball_tree')
    nn.fit(df[['latitude', 'longitude']])
    distances, indices = nn.kneighbors([[lat, long]])
    closest_points = df.iloc[indices[0]]
    return closest_points

def main():
    st.title('Discover Your Next Home')
    api_key = os.getenv("OPENAI_API_KEY")  # Load the API key from environment variables
    df = load_data()

    if df.empty:
        st.write("No data available with valid addresses.")
        st.stop()

    target_address = st.text_input("Enter a target address")
    num_neighbors = st.number_input('Number of closest apartments to find', min_value=1, max_value=15, value=10, step=1)

    if 'email_sent' not in st.session_state:
        st.session_state['email_sent'] = False

    if st.button('Find Apartments Nearby'):
        st.session_state['email_sent'] = False  # Reset email sent state on new search
        user_lat, user_long = geocode_address(target_address, api_key)
        if user_lat is None or user_long is None:
            st.error("Unable to find the specified address. Please provide a valid address.")
            st.stop()
        
        closest_points = get_nearest_apartments(df, user_lat, user_long, num_neighbors)
        st.session_state['closest_points'] = closest_points  # Store in session state to avoid recomputation

    if 'closest_points' in st.session_state:
        closest_points_display = st.session_state['closest_points'].reset_index(drop=True)
        closest_points_display.index += 1  # Shift index to start from 1
        st.write(f'The info for closest {num_neighbors} apartments:')
        st.write(closest_points_display[['address', 'bedrooms', 'bathrooms', 'square_feet', 'price_display']])
        st.map(st.session_state['closest_points'])

    email = st.text_input("Enter your email address to receive the apartment listings:")
    if st.button('Send Info To Me'):
        if not validate_email(email):
            st.info("Please input a valid email address.")
            return
        if 'closest_points' not in st.session_state:
            st.info("No apartments data.")
            return
        send_email(st, email, closest_points_display[['address', 'bedrooms', 'bathrooms', 'square_feet', 'price_display']].values.tolist())
        st.session_state['email_sent'] = True  # Update state to prevent multiple sends

if __name__ == "__main__":
    main()
