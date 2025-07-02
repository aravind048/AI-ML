# api.py

import requests
from config import API_BASE_URL


def get_all_products():
    try:
        res = requests.get(API_BASE_URL)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        print(f"❌ Error fetching products: {e}")
        return []


def get_product_by_id(product_id: str):
    """Fetch a specific product by ID"""
    try:
        url = f"{API_BASE_URL}/{product_id}"
        res = requests.get(url)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        print(f"❌ Error fetching product ID {product_id}: {e}")
        return None


def create_product(name: str, price: str, description: str):
    payload = {
        "name": name,
        "price": price,
        "description": description
    }
    try:
        res = requests.post(API_BASE_URL, json=payload)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        print(f"❌ Error creating product: {e}")
        return None


def update_product(product_id: str, name=None, price=None, description=None):
    payload = {}
    if name:
        payload["name"] = name
    if price:
        payload["price"] = price
    if description:
        payload["description"] = description

    if not payload:
        print("❗ No fields to update.")
        return None

    try:
        url = f"{API_BASE_URL}/{product_id}"
        res = requests.put(url, json=payload)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        print(f"❌ Error updating product: {e}")
        return None


def delete_product(product_id: str) -> bool:
    try:
        url = f"{API_BASE_URL}/{product_id}"
        print(f"📡 Sending DELETE request to: {url}")  # ✅ URL log

        response = requests.delete(url)

        # ✅ Log everything about the response
        print(f"🔁 Status Code: {response.status_code}")
        print(f"📨 Response Text: {response.text}")

        # ✅ Return True only if deletion actually succeeded
        return response.status_code in {200, 204}

    except requests.RequestException as e:
        print(f"❌ Exception during deletion: {e}")
        return False
