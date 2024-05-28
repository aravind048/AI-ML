import string
import re
import json
import requests
from textblob import TextBlob
from sklearn.ensemble import RandomForestClassifier
from joblib import load
import numpy as np

# Function to preprocess text data
def preprocess_text(text):
    text = text.translate(str.maketrans('', '', string.punctuation))
    text = text.lower()
    text = re.sub('\s+', ' ', text).strip()
    return text

# Function to fetch user reviews data from Google Maps API
def fetch_user_reviews(place_id, api_key):
    url = f'https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=reviews&key={api_key}'
    response = requests.get(url)
    if response.status_code == 200:
        reviews_data = response.json().get('result', {}).get('reviews', [])
        return reviews_data
    else:
        print("Failed to fetch user reviews data.")
        return None

# Function to fetch place ID from Google Maps API
def fetch_place_id(location, api_key):
    url = f'https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={location}&inputtype=textquery&fields=place_id&key={api_key}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if 'candidates' in data and len(data['candidates']) > 0:
            return data['candidates'][0]['place_id']
        else:
            print("No candidates found for the location.")
            return None
    else:
        print("Failed to fetch Place ID. Status code:", response.status_code)
        return None

# Define the API key
api_key = ''

# Define the location you want to search for
location = 'India gate, New Delhi'

# Fetch the place ID
place_id = fetch_place_id(location, api_key)

if place_id:
    print("Place ID:", place_id)
    
    # Fetch user reviews data
    user_reviews = fetch_user_reviews(place_id, api_key)
    if user_reviews:
        print("User Reviews Data:")
        print(json.dumps(user_reviews, indent=4))
        
        # Preprocess each review
        preprocessed_reviews = [preprocess_text(review['text']) for review in user_reviews]
        print("\nPreprocessed Reviews:")
        print(preprocessed_reviews)
        
        # Load the trained sentiment analysis model
        sentiment_classifier = load('sentimodel.pkl')
        
        # Convert text data into numerical features using sentiment polarity
        X_new = np.array([TextBlob(review).sentiment.polarity for review in preprocessed_reviews]).reshape(-1, 1)
        
        # Predict sentiment for each review
        sentiments = []
        for review, X in zip(user_reviews, X_new):
            sentiment = sentiment_classifier.predict([X])[0]
            sentiments.append(sentiment)
        
        # Specify the output file path
        output_file_path = 'output.txt'
        
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write("User Reviews Data:\n")
            f.write(json.dumps(user_reviews, indent=4, ensure_ascii=False))
            f.write("\n\n")
            
            f.write("Preprocessed Reviews:\n")
            f.write("\n".join(preprocessed_reviews))
            f.write("\n\n")
            
            f.write("Sentiment Analysis Results:\n")
            for review, sentiment in zip(user_reviews, sentiments):
                f.write(f"Review: {review['text']}\n")
                f.write(f"Predicted Sentiment: {sentiment}\n")
                f.write("------------\n")
        
        print(f"Output written to {output_file_path}")
    else:
        print("No user reviews found.")
else:
    print("Failed to fetch place ID.")
