# parser.py

from config import llm
import json
import re

def parse_user_input(user_input: str) -> dict:
    """
    Use Gemini to extract intent and product details from natural language input.
    Returns a structured dict with:
    - intent: list, create, update, delete
    - product_id: str or None
    - name: str or None
    - price: str or None
    - description: str or None
    """
    prompt = f"""
You are a product management assistant. A user will give you a command in natural language.
Your task is to extract structured data from it.

User Input: "{user_input}"

Respond in the following JSON format (only output JSON, nothing else):

{{
  "intent": "list" | "create" | "update" | "delete",
  "product_id": "string or null",
  "name": "string or null",
  "price": "string or null",
  "description": "string or null"
}}
"""

    try:
        response = llm.invoke(prompt)
        content = response.content

        # 🔍 Convert list to string if needed
        if isinstance(content, list):
            content = " ".join(str(item) for item in content)

        if not isinstance(content, str):
            raise ValueError("Gemini returned unexpected response format.")

        # 🧼 Extract JSON block from Gemini response
        match = re.search(r"\{.*\}", content, re.DOTALL)
        json_text = match.group(0) if match else content

        parsed = json.loads(json_text)

        return {
            "intent": parsed.get("intent"),
            "product_id": parsed.get("product_id"),
            "name": parsed.get("name"),
            "price": parsed.get("price"),
            "description": parsed.get("description")
        }

    except Exception as e:
        print("❌ Failed to parse input:", e)
        return {
            "intent": None,
            "product_id": None,
            "name": None,
            "price": None,
            "description": None
        }
