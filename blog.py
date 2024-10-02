from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import requests
from dotenv import load_dotenv
from openai import OpenAI  # Use the new OpenAI client

load_dotenv()

api_key = os.getenv("API_KEY")
endpoint = os.getenv("BASE_URL")

app = FastAPI()

# create an instance of the Openai client
client = OpenAI(api_key=api_key, base_url=endpoint)

class ChatRequest(BaseModel):
    user_message: str

@app.post("/generate-response/")
async def generate_response(request: ChatRequest):
    try:
        # calling openai API directly to get a response using the messages parameter
        completion = client.chat.completions.create(
            model=os.getenv("MODEL"),
            messages=[
                {"role": "system", "content": "You are a tourist who give blogs."},
                {"role": "user", "content": request.user_message}
            ],
            max_tokens=512,
            top_p=0.8,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        
        try:
            url=os.getenv("UNPLASH_BASE_URL")
            headers = {
                "Authorization": f"Client-ID {os.getenv('UNPLASH_ACCESS_KEY')}"
            }
            
            params={
                "query": request.user_message,
                "per_page": 2
            }
            
            unsplash_response = requests.get(url, headers=headers, params=params)
            
            if unsplash_response.status_code == 200:
                unsplash_data = unsplash_response.json()
                image_urls = [photo['urls']['regular'] for photo in unsplash_data['results']]
            
            else:
                image_urls = []
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"unsplash API error: {str(e)}")        
            
        
        #reponses
        return {
            "response": completion.choices[0].message.content,
            "usage": dict(completion).get('usage'),  # Include usage information if needed
            "image_urls": image_urls
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Running
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
