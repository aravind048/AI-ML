import requests
from textblob import TextBlob
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold
from imblearn.over_sampling import RandomOverSampler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import numpy as np
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer

place_id = 'ChIJb1u6CbJfUjoRyludAlSWRSw'  # Example place ID
api_key = ''  # Replace with your actual API key

url = f'https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&key={api_key}'
response = requests.get(url)

if response.status_code == 200:
    location_data = response.json()['result']
    reviews = [review['text'] for review in location_data.get('reviews', [])]
else:
    print("Failed to fetch location details. Status code:", response.status_code)
    exit()

sentiments = []
for review in reviews:
    analysis = TextBlob(review)
    polarity = analysis.sentiment.polarity
    if polarity > 0:
        sentiments.append('positive')
    elif polarity < 0:
        sentiments.append('negative')
    else:
        sentiments.append('neutral')

X = np.array([TextBlob(review).sentiment.polarity for review in reviews]).reshape(-1, 1)
y = np.array(sentiments)

# Check the class distribution before RandomOverSampler
unique_classes = np.unique(y, return_counts=True)
print("Class Distribution Before RandomOverSampler:", dict(zip(unique_classes[0], unique_classes[1])))

# Apply RandomOverSampler
random_oversampler = RandomOverSampler(random_state=42)
X_resampled, y_resampled = random_oversampler.fit_resample(X, y)

# Check the class distribution after RandomOverSampler
unique_classes_resampled = np.unique(y_resampled, return_counts=True)
print("Class Distribution After RandomOverSampler:", dict(zip(unique_classes_resampled[0], unique_classes_resampled[1])))

vectorizer = TfidfVectorizer()
classifier = RandomForestClassifier(random_state=42)

# Use StratifiedKFold with adjusted number of splits based on the minority class size
min_class_size = min(unique_classes_resampled[1])  # Minimum number of samples in any class after oversampling
n_splits = min(5, min_class_size)  # Use at most 5 splits or the minimum class size, whichever is smaller
skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)

cv_scores = []
for train_index, test_index in skf.split(X_resampled, y_resampled):
    X_train, X_test = X_resampled[train_index], X_resampled[test_index]
    y_train, y_test = y_resampled[train_index], y_resampled[test_index]

    classifier.fit(X_train, y_train)
    y_pred = classifier.predict(X_test)
    cv_scores.append(accuracy_score(y_test, y_pred))

mean_cv_accuracy = np.mean(cv_scores)
print("Cross-Validation Scores:", cv_scores)
print("Mean CV Accuracy:", mean_cv_accuracy)

# Fit the classifier on the entire resampled dataset
classifier.fit(X_resampled, y_resampled)

# Make predictions
y_pred = classifier.predict(X_resampled)

# Calculate evaluation metrics
accuracy = accuracy_score(y_resampled, y_pred)
precision = precision_score(y_resampled, y_pred, average='weighted')
recall = recall_score(y_resampled, y_pred, average='weighted')
f1 = f1_score(y_resampled, y_pred, average='weighted')

print("Evaluation Metrics:")
print(f"Accuracy: {accuracy}")
print(f"Precision: {precision}")
print(f"Recall: {recall}")
print(f"F1 Score: {f1}")

joblib.dump(classifier, 'sentimodel.pkl')
joblib.dump(vectorizer, 'vectorizer.pkl')
