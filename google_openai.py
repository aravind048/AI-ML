import openai
import requests
import googlemaps

# Initialize the OpenAI API key
openai.api_key = ''

# Initialize the Google Maps API key
gmaps = googlemaps.Client(key='')

def collect_user_preferences():
    purposes = input("Enter purpose of visit (honeymoon, family holiday, business, solo, weekend, with partner): ").strip().split(',')
    start_date = input("Enter start date (YYYY-MM-DD): ").strip()
    start_time = input("Enter start time (HH:MM): ").strip()
    end_date = input("Enter end date (YYYY-MM-DD): ").strip()
    end_time = input("Enter end time (HH:MM): ").strip()
    pace_of_day = input("Enter pace of the day (leisurely, moderate, packed): ").strip()
    interests = input("Enter interests (comma-separated from Museum, Shopping, Local Cuisine, History, Architecture, Music): ").strip().split(',')
    budget = input("Enter budget ($, $$, $$$, $$$$): ").strip()
    itinerary_preference = input("Would you like a detailed itinerary? (yes/no): ").strip().lower()
    return purposes, start_date, start_time, end_date, end_time, pace_of_day, interests, budget, itinerary_preference

def get_currency_for_location(location):
    currency_mapping = {
        'Tamil Nadu': 'INR',
        'Meghalaya': 'INR',
        'Singapore': 'SGD',
        'United States': 'USD'
    }
    return currency_mapping.get(location, 'INR')

def get_currency_symbol(currency_code):
    currency_symbol_mapping = {
        'INR': '₹',
        'SGD': 'S$',
        'USD': '$',
        'EUR': '€',
        'GBP': '£'
    }
    return currency_symbol_mapping.get(currency_code, currency_code)

def convert_budget_to_local_currency(budget, local_currency):
    budget_mapping = {
        '$': 'Budget-friendly',
        '$$': 'Moderate',
        '$$$': 'Luxury',
        '$$$$': 'Ultra Luxury'
    }
    local_currency_symbol = get_currency_symbol(local_currency)
    return f"{budget_mapping[budget]} ({local_currency_symbol})"

def get_suggestions_from_rag(purposes, start_date, start_time, end_date, end_time, pace_of_day, interests, budget, locations, itinerary_preference, places_info):
    local_currency = get_currency_for_location(locations[0])  # Assuming all locations use the same currency for simplicity
    budget_localized = convert_budget_to_local_currency(budget, local_currency)
    
    prompt = (
        f"I am planning a trip with the following preferences:\n"
        f"Purpose of Visit: {', '.join(purposes)}\n"
        f"Time Duration: From {start_date} {start_time} to {end_date} {end_time}\n"
        f"Pace of the Day: {pace_of_day}\n"
        f"Interests: {', '.join(interests)}\n"
        f"Budget: {budget_localized}\n"
        f"Locations: {', '.join(locations)}\n"
        f"Places of Interest: {', '.join(places_info)}\n"
        f"Can you suggest must visit or top rated places to visit that match these preferences? Please include the exact names of hotels, restaurants, attractions, exact flight timings, train timings, and their respective fares or prices as per the location.\n"
        f"Also, list out all events happening during my visit as per the location on the preferences.\n"
    )
    
    if itinerary_preference == "yes":
        prompt += "\nPlease provide a detailed itinerary for my trip with specific timings for each activity, including the exact names of hotels, restaurants, attractions, their respective fares or prices, and events."

    # Using OpenAI for now as a placeholder for RAG model
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=2000  # Increased token limit for more detailed responses
    )
    suggestions = response.choices[0].message['content'].strip()
    return suggestions

def fetch_weather(location, api_key):
    base_url = f"http://api.weatherapi.com/v1/current.json"
    params = {
        "q": location,
        "key": api_key
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        return data.get('current', {})
    else:
        print(f"Failed to fetch weather for {location}. Status code: {response.status_code}")
        return {}

def get_google_places(location, interests):
    places = []
    geocode_result = gmaps.geocode(location)
    if geocode_result:
        lat_lng = geocode_result[0]['geometry']['location']
        for interest in interests:
            places_result = gmaps.places_nearby(location=lat_lng, radius=5000, keyword=interest)
            for place in places_result['results']:
                places.append(place['name'])
    return places

def search_and_write_places(locations, purposes, start_date, start_time, end_date, end_time, pace_of_day, interests, budget, itinerary_preference, output_file, weather_api_key=None):
    with open(output_file, 'w', encoding='utf-8') as file:
        combined_weather_info = ""
        all_places_info = []
        for location in locations:
            # Fetch weather information for the location
            weather_data = fetch_weather(location, weather_api_key)
            if weather_data:
                combined_weather_info += f"Current Weather in {location}: {weather_data.get('condition', {}).get('text', '')}, Temperature: {weather_data.get('temp_c', '')}°C\n"
            else:
                combined_weather_info += f"Weather information not available for {location}\n"

            # Fetch Google Places information for the location
            places_info = get_google_places(location, interests)
            all_places_info.extend(places_info)
            file.write(f"Places to visit in {location} based on interests ({', '.join(interests)}):\n")
            for place in places_info:
                file.write(f"- {place}\n")
            file.write("\n")

        file.write(f"Search results for {', '.join(locations)}:\n\n")
        file.write(combined_weather_info + "\n")

        # Generate suggestions using GPT-4 based on user preferences and places info
        suggestions = get_suggestions_from_rag(purposes, start_date, start_time, end_date, end_time, pace_of_day, interests, budget, locations, itinerary_preference, all_places_info)
        file.write(f"Suggestions from ChatGPT:\n{suggestions}\n\n")

# Example usage
weather_api_key = ''
locations = ['Singapore']

# Collect user preferences dynamically
purposes, start_date, start_time, end_date, end_time, pace_of_day, interests, budget, itinerary_preference = collect_user_preferences()

output_file = 'places_output.txt'

# Perform search and write places for each location
search_and_write_places(locations, purposes, start_date, start_time, end_date, end_time, pace_of_day, interests, budget, itinerary_preference, output_file, weather_api_key)

print(f"Output written to {output_file}")
