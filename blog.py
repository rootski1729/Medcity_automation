from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import requests
import random
import firebase_admin
from firebase_admin import credentials, firestore, storage
from dotenv import load_dotenv
import cohere
load_dotenv()

# Initialize Firebase
cred = credentials.Certificate(os.getenv("FIREBASE_CREDENTIALS_PATH"))
firebase_admin.initialize_app(cred, {'storageBucket': f"{os.getenv('FIREBASE_PROJECT_ID')}.firebasestorage.app"})
db = firestore.client()
bucket = storage.bucket()

# Initialize Cohere
cohere_api_key = os.getenv("COHERE_API_KEY")
cohere_client = cohere.Client(cohere_api_key)

def get_random_input():
    keywords_ref = db.collection('keyword').stream()
    keyword_list = [doc.to_dict().get("phrase") for doc in keywords_ref]
    
    if not keyword_list:
        return None
    return random.choice(keyword_list)

def generate_blog_content(keyword):
    try:
        response = cohere_client.generate(
            model="command",
            prompt= f"""You are a tourist who writes blogs. {keyword} Write a blog about it with suitable title.
            Format the response like this:
            
            Title: <Catchy blog title>
            
            Content:
            <Blog content here>""",
            max_tokens=520,
            temperature=0.8,
            k=0,
            p=0.8,
            stop_sequences=["--"]
        )
        return response.generations[0].text
    except Exception as e:
        return None

def fetch_image(keyword):
    url = os.getenv("UNSPLASH_BASE_URL")
    headers = {
        "Authorization" : f"Client-ID {os.getenv('UNSPLASH_ACCESS_KEY')}"}
    params = {
        "query": keyword,
        "per_page": 1
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        return []

    data = response.json()
    return [photo['urls']['regular'] for photo in data['results']] 

def upload_image(image_url, keyword):
    response = requests.get(image_url, stream=True)
    if response.status_code != 200:
        return None
    
    blob = bucket.blob(f"blogs_img/{keyword}.jpg")
    blob.upload_from_file(response.raw, content_type="image/jpeg")
    blob.make_public()
    return blob.public_url


def main():
    keyword = get_random_input()
    if not keyword:
        keyword = "trip to banaras uttar pradesh India" 

    blog_content = generate_blog_content(keyword)
    if not blog_content:
        return None
    image_urls = fetch_image(keyword)
    image_url = upload_image(image_urls[0], keyword)

    blog_data = {
        "blog_description": blog_content,
        "blog_image": image_url
    }

    db.collection('blog').add(blog_data)


if __name__ == "__main__":
    main()
