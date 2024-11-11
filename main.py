# ChatGPT was used for most of this code
# This is for demonstration

import streamlit as st
import pandas as pd
import pydeck as pdk
import os
from geopy.geocoders import Nominatim
import time
import kagglehub


# check if file exists
file_path = 'aqi_geo.csv'
if not os.path.exists(file_path):
   print("File does not exist.")
   
   # Download latest version
   path = kagglehub.dataset_download("dnkumars/air-quality-index")
   df = pd.read_csv(path+'\\aqi_data.csv')


   # Initialize the geolocator
   geolocator = Nominatim(user_agent="geoapi")

   # Function to get latitude and longitude from city name
   def get_location(city_name):
      location = geolocator.geocode(city_name)
      if location:
         time.sleep(2)
         print(city_name)
         return location.latitude, location.longitude
      else:
         return None, None

   df[['latitude', 'longitude']] = df['city'].apply(lambda x: pd.Series(get_location(x)))
   
   df.to_csv('aqi_geo.csv', index=False)



data = pd.read_csv('aqi_geo.csv')

# Convert to DataFrame
df = pd.DataFrame(data)

# Title and description
st.title("City Air Quality Visualization")
st.subheader("Tyler Gabriel")
st.markdown("""
This app allows the user to explore various relationships between data concerning air quality index (AQI) across various cities.
""")


st.subheader("Simple Paginated Table")
st.markdown("""
This table allows the user to navigate through the data (sorted by AQI rank) to have a simple view of the various values for each city. Simply enter a page number (10 per page) to nagivate to a new page.
""")


# Pagination for the table
page_size = 10  # Number of rows per page
num_pages = len(df) // page_size + (1 if len(df) % page_size != 0 else 0)

page_input = st.text_input("Enter page number", "1")

# Validate the input to ensure it’s a valid integer
try:
    page = int(page_input)
    # Ensure the page number is within the valid range
    if page < 1:
        page = 1
    elif page > num_pages:
        page = num_pages
except ValueError:
    page = 1  # Default to the first page if input is invalid

# Display the relevant subset of the DataFrame
start_row = (page - 1) * page_size
end_row = start_row + page_size
st.dataframe(df.iloc[start_row:end_row])





st.subheader("City Search tool")
st.markdown("""
This table allows the user to search for a particular city (if it included within the data) in the (city_name,country_name) form. The respective data is shown in the table if there is a match (upon pressing enter), otherwise the table will be empty.
""")


# Create a search box to filter cities
search_query = st.text_input("Search for a city")

# If there's no query, show an empty DataFrame
if search_query:
    filtered_df = df[df['city'].str.contains(search_query, case=False, na=False)]
else:
    filtered_df = pd.DataFrame()  # Empty DataFrame by default

# Display the filtered dataframe (will be empty initially)
st.dataframe(filtered_df)


st.subheader("Interactive AQI Map")
st.markdown("""
This map visualizes cities based on their latitude and longitude with colors representing the average AQI (blue = low, red = high). 
You can also use the slider to explore monthly AQI variations. Additionally, select the checkbox to reveal the month slider to see values by month.
""")



# Month selection with an optional slider
month_option = st.checkbox("Show monthly data")
if month_option:
   month = st.slider("Select Month", 1, 12, 1, format="%d")
   month_abbr = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
   selected_month = month_abbr[month - 1]
   df['aqi'] = df[selected_month]
else:
   df['aqi'] = df['avg']

# Ensure the column is numeric and handle non-numeric values
df['aqi'] = pd.to_numeric(df['aqi'], errors='coerce')  # This will convert invalid values to NaN

# Optionally, fill NaN values with a default value (e.g., 0)
df['aqi'] = df['aqi'].fillna(0)

# Now apply the color logic after ensuring all data is numeric
min_aqi = df['aqi'].min()
max_aqi = df['aqi'].max()

df['color'] = df['aqi'].apply(lambda aqi: [
    int((aqi - min_aqi) / (max_aqi - min_aqi) * 255),  # Red channel
    0,  # Green channel
    int(255 - (aqi - min_aqi) / (max_aqi - min_aqi) * 255)  # Blue channel
])


# Define the layer for the map
layer = pdk.Layer(
   "ScatterplotLayer",
   data=df,
   get_position="[longitude, latitude]",
   get_radius=10000,  # Radius of circles
   get_fill_color="color",  # Color by aqi
   pickable=True
)

# Set up the view for the map
view_state = pdk.ViewState(
   latitude=df['latitude'].mean(),
   longitude=df['longitude'].mean(),
   zoom=4,
   pitch=0
)

# Render the map with tooltip showing city and aqi
st.pydeck_chart(pdk.Deck(
   layers=[layer],
   initial_view_state=view_state,
   tooltip={"text": "{city}\nAQI: {aqi}"}
))


# Section header and description
st.subheader(f"Top and Bottom Cities by Average AQI")
st.markdown("""
Below are the cities with the highest and lowest average AQI values based on the number you selected with the slider.
""")


# Create a slider to control the number of top/bottom cities displayed
n_cities = st.slider("Select number of top/bottom cities to display", min_value=1, max_value=10, value=5)

# Sort the DataFrame by 'avg' to get top and bottom cities based on the slider value
top_cities = df.nlargest(n_cities, 'avg')  # Top n cities by avg aqi
bottom_cities = df.nsmallest(n_cities, 'avg')  # Bottom n cities by avg aqi


# Combine the top and bottom cities for display
combined_df = pd.concat([top_cities, bottom_cities])

# Display the small table
st.dataframe(combined_df[['city', 'avg']])  # Only show city and avg columns

st.subheader(f"Conclusion")
st.markdown("""
Ultimately, it appears as if parts of the "developing world" appear to have higher AQIs, which may indicate less regulation on enivonrment pollutants and/or a reliance on fossil fuels for energy generation. Additionally, the map also indicates that AQI appears to be higher in areas known to have high urban density.
""")
