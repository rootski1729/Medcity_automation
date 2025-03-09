import uuid
import os
import requests
import random
import firebase_admin
from firebase_admin import credentials, firestore, storage
from dotenv import load_dotenv
import cohere
import datetime
load_dotenv()


#Initialize Firebase

def initialize_firebase_app(credential_path, app_name, project_id):
    cred = credentials.Certificate(credential_path)
    return firebase_admin.initialize_app(
        cred,
        {'storageBucket': f"{project_id}.firebasestorage.app"},
        name =  app_name
    )

#hotel soni
app1 = initialize_firebase_app(
    os.getenv("FIREBASE_CREDENTIALS_PATH_SONI"),
    "project1",
    os.getenv("FIREBASE_PROJECT_ID_SONI")
)

#hotel jbm
app2 = initialize_firebase_app(
    os.getenv("FIREBASE_CREDENTIALS_PATH_jbm"),
    "project2",
    os.getenv("FIREBASE_PROJECT_ID_jbm")
)


# Initialize Cohere
cohere_api_key = os.getenv("COHERE_API_KEY")
cohere_client = cohere.Client(cohere_api_key)

def get_firestore_client(app):
    return firestore.client(app=app)

def get_storage_bucket(app):
    return storage.bucket(app=app)
#get random keyword
def get_random_input(app):
    db = get_firestore_client(app)
    keywords_ref = db.collection('keyword').stream()
    keyword_list = [doc.to_dict().get("phrase") for doc in keywords_ref]
    
    if not keyword_list:
        return None
    return random.choice(keyword_list)


#genrate blog
def generate_blog_content(keyword):
    try:
        response = cohere_client.generate(
            model="command",
            prompt= f"""You are a tourist who writes blogs. {keyword} Write a blog about it with suitable title.
            Format the response like this:
            
            Title: <Catchy blog title>
            
            Content:
            <Blog content here with beautiful ending>""",
            max_tokens=300,
            temperature=0.8,
            k=0,
            p=0.8,
            stop_sequences=["End of blog"]
        )
        
        generated_text = response.generations[0].text
        
        title = None
        content = None
        
        if "Title:" in generated_text and "Content:" in generated_text:
            title, content = generated_text.split("Content:")
            title = title.split("Title:")[1].strip()
            content = content.strip()
            
        return title, content
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

def upload_image(app,image_url, keyword):
    bucket = get_storage_bucket(app)
    response = requests.get(image_url, stream=True)
    if response.status_code != 200:
        return None

    unique_id = uuid.uuid4().hex
    blob = bucket.blob(f"blogs_img/{keyword}_{unique_id}.jpg")
    blob.upload_from_file(response.raw, content_type="image/jpeg")
    blob.make_public()
    return blob.public_url

def save_blog(app,blog_data):
    db = get_firestore_client(app)
    db.collection('blog').add(blog_data)


def main(app):
    keyword = get_random_input(app)
    if not keyword:
        keyword = "trip to banaras uttar pradesh India" 

    title,content = generate_blog_content(keyword)
    
    if not title or not content:
        return None
    image_urls = fetch_image(keyword)
    image_url = upload_image(app,image_urls[0], keyword)

    blog_data = {
        "title": title.lower(),
        "description": content,
        "image": image_url,
        "createdAt" : datetime.datetime.now()
    }

    save_blog(app, blog_data)


if __name__ == "__main__":
    main(app1)
    main(app2)
