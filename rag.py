from flask import Flask, request, jsonify
import openai
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import aiohttp
import asyncio
from datetime import datetime

app = Flask(__name__)

openai.api_key = ""  # Replace with your actual OpenAI API key

# Function to fetch and directly tokenize an article from a single URL
async def fetch_and_tokenize_article_async(url):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                paragraphs = [para.get_text() for para in soup.find_all('p') if para.get_text().strip()]
                return paragraphs
        except aiohttp.ClientError as e:
            print(f"Error fetching article from {url}: {e}")
            return []

# Function to fetch and tokenize multiple articles in parallel
async def fetch_and_tokenize_articles_async(urls):
    tasks = [fetch_and_tokenize_article_async(url) for url in urls]
    tokenized_articles = await asyncio.gather(*tasks)
    return tokenized_articles

# Function to vectorize the chunks and return the vectorizer and vectors
def vectorize_articles(tokenized_articles):
    vectorizer = TfidfVectorizer()
    all_chunks = [chunk for article in tokenized_articles for chunk in article]
    vectors = vectorizer.fit_transform(all_chunks)
    print(f"TF-IDF Vectors Shape: {vectors.shape}")

    return vectorizer, vectors, all_chunks

# Function to retrieve the most relevant chunks from multiple articles
def retrieve_relevant_chunks_multiple_articles(question, vectorizer, vectors, all_chunks, top_n=3):
    question_vector = vectorizer.transform([question])
    similarities = cosine_similarity(question_vector, vectors).flatten()
    relevant_indices = similarities.argsort()[-top_n:][::-1]
    relevant_chunks = [all_chunks[i] for i in relevant_indices]
    return "\n".join(relevant_chunks)

# Function to create the prompt
def create_prompt(relevant_text, question):
    prompt = (
        f"Please read the following text carefully and answer the question based only on the information provided:\n\n"
        f"Text:\n{relevant_text}\n\n"
        f"Question: {question}\n\n"
        f"Answer the question using the information from the text:"
    )
    return prompt

# Function to generate the answer using the chat completions API
async def generate_answer_async(prompt):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.openai.com/v1/chat/completions",
            json={
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that answers questions based strictly on provided articles."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 150
            },
            headers={"Authorization": f"Bearer {openai.api_key}"}
        ) as response:
            result = await response.json()
            # Extract the answer and the tokens used
            answer = result['choices'][0]['message']['content'].strip()
            tokens_used = result['usage']['total_tokens']
            return answer, tokens_used

# Function to generate answers for multiple prompts asynchronously
async def generate_answers_async(prompts):
    tasks = [generate_answer_async(prompt) for prompt in prompts]
    return await asyncio.gather(*tasks)

# Flask route to handle requests
@app.route('/rag', methods=['POST'])
async def ask_question():
    data = request.json
    urls = data.get('urls', [])
    questions = data.get('questions', [])
    
    if not urls or not questions:
        return jsonify({"error": "Please provide both 'urls' and 'questions' in the request body."}), 400
    
    tokenized_articles = await fetch_and_tokenize_articles_async(urls)
    vectorizer, vectors, all_chunks = vectorize_articles(tokenized_articles)
    
    prompts = []
    for question in questions:
        relevant_text = retrieve_relevant_chunks_multiple_articles(question, vectorizer, vectors, all_chunks)
        prompt = create_prompt(relevant_text, question)
        prompts.append(prompt)
    
    # Generate answers asynchronously
    results = await generate_answers_async(prompts)
    
    # Get the current time (last update time)
    last_updated = datetime.now().isoformat()
    
    # Prepare the answers and accumulate the total tokens used
    answers = []
    total_tokens_used = 0
    for (q, (a, tokens)) in zip(questions, results):
        answers.append({"question": q, "answer": a})
        total_tokens_used += tokens
    
    return jsonify({
        "last_updated": last_updated,
        "total_tokens_used": total_tokens_used,
        "answers": answers
    })

if __name__ == '__main__':
    app.run(debug=True)