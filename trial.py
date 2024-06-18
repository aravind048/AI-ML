import openai
import requests

# Initialize the OpenAI API key
openai.api_key = ''

def collect_user_preferences():
    activities = input("Enter preferred activities (comma-separated): ").strip().split(',')
    destination_types = input("Enter preferred destination types (comma-separated): ").strip().split(',')
    trip_duration = int(input("Enter trip duration (in days): "))
    accommodation = input("Enter accommodation preferences: ").strip()
    transportation = input("Enter transportation preferences: ").strip()
    season = input("Enter preferred season for travel: ").strip()
    budget = input("Enter your budget: ").strip()
    cultural_language_preferences = input("Enter cultural and language preferences: ").strip()
    safety_security = input("Enter safety and security preferences: ").strip()
    accessibility = input("Enter accessibility preferences: ").strip()
    solo_or_group = input("Is this a solo or group travel? ").strip()
    ask_itinerary = input("Do you want an itinerary for your trip? (yes/no): ").strip().lower() == 'yes'
    
    return (activities, destination_types, trip_duration, accommodation, transportation, season, budget, 
            cultural_language_preferences, safety_security, accessibility, solo_or_group, ask_itinerary)

def get_suggestions_from_chatgpt(activities, destination_types, trip_duration, location, 
                                 accommodation, transportation, season, budget, 
                                 cultural_language_preferences, safety_security, 
                                 accessibility, solo_or_group, ask_itinerary):
    prompt = (
        f"I am planning a trip to {location} with the following preferences:\n"
        f"Activities: {', '.join(activities)}\n"
        f"Destination Types: {', '.join(destination_types)}\n"
        f"Trip Duration: {trip_duration} days\n"
        f"Accommodation: {accommodation}\n"
        f"Transportation: {transportation}\n"
        f"Season: {season}\n"
        f"Budget: {budget}\n"
        f"Cultural and Language Preferences: {cultural_language_preferences}\n"
        f"Safety and Security: {safety_security}\n"
        f"Accessibility: {accessibility}\n"
        f"Solo or Group Travel: {solo_or_group}\n"
        f"{'Please also provide a detailed itinerary for the trip.' if ask_itinerary else ''}\n"
        f"Can you suggest some places to visit and events to attend?"
    )

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500
    )
    
    suggestions = response.choices[0].message['content'].strip()
    return suggestions

def fetch_weather(location, api_key):
    base_url = "http://api.weatherapi.com/v1/current.json"
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

def search_and_write_places(locations, activities, destination_types, output_file, trip_duration=0, weather_api_key=None,
                            accommodation=None, transportation=None, season=None, budget=None, 
                            cultural_language_preferences=None, safety_security=None, 
                            accessibility=None, solo_or_group=None, ask_itinerary=False):
    with open(output_file, 'w', encoding='utf-8') as file:
        for location in locations:
            file.write(f"Search results for {location} (Trip Duration: {trip_duration}):\n\n")
            
            # Fetch and print weather information for the location
            if weather_api_key:
                weather_data = fetch_weather(location, weather_api_key)
                if weather_data:
                    weather_info = f"Current Weather for {location}: {weather_data.get('condition', {}).get('text', '')}, Temperature: {weather_data.get('temp_c', '')}°C\n\n"
                else:
                    weather_info = "Weather information not available\n\n"
            else:
                weather_info = "Weather information not provided.\n\n"
            
            file.write(weather_info)
            
            # Generate suggestions using ChatGPT
            suggestions = get_suggestions_from_chatgpt(activities, destination_types, trip_duration, location, 
                                                       accommodation, transportation, season, budget, 
                                                       cultural_language_preferences, safety_security, 
                                                       accessibility, solo_or_group, ask_itinerary)
            file.write(f"Suggestions from ChatGPT for {location}:\n\n{suggestions}\n\n")
            
            # Extract events from the suggestions (assuming they are marked in the response)
            file.write("Events:\n\n")
            if "Events:" in suggestions:
                events_section = suggestions.split("Events:")[1].strip()
                file.write(events_section + "\n\n")
            else:
                file.write("No specific events mentioned.\n\n")

            file.write("\n")  # Add newline after each location's results

    if not ask_itinerary:
        ask_for_itinerary = input("Would you like an itinerary for your trip? (yes/no): ").strip().lower()
        if ask_for_itinerary == 'yes':
            # If user wants an itinerary, generate it and append to the output file
            with open(output_file, 'a', encoding='utf-8') as file:
                file.write("\nDetailed Itinerary:\n\n")
                itinerary = get_suggestions_from_chatgpt(activities, destination_types, trip_duration, location, 
                                                         accommodation, transportation, season, budget, 
                                                         cultural_language_preferences, safety_security, 
                                                         accessibility, solo_or_group, True)
                file.write(itinerary + "\n")

# Example usage
weather_api_key = ''
locations = ['Tamil Nadu']

# Collect user preferences dynamically
(preferred_activities, preferred_destination_types, trip_duration, accommodation, transportation, season, budget, 
 cultural_language_preferences, safety_security, accessibility, solo_or_group, ask_itinerary) = collect_user_preferences()

output_file = 'places_output.txt'

# Perform search and write places for each location
search_and_write_places(locations, preferred_activities, preferred_destination_types, output_file, trip_duration, 
                        weather_api_key, accommodation, transportation, season, budget, cultural_language_preferences, 
                        safety_security, accessibility, solo_or_group, ask_itinerary)

print(f"Output written to {output_file}")
