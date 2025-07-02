import os
from langchain_google_genai import ChatGoogleGenerativeAI

# Set your Google API Key
os.environ["GOOGLE_API_KEY"] = ""

# Initialize Gemini model
llm = ChatGoogleGenerativeAI(
    model="learnlm-2.0-flash-experimental",
    temperature=0.2
)

# Base URL for mock API
API_BASE_URL = "https://65c1ba86dc74300bce8dd895.mockapi.io/api/v1/products"