from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import requests
from dotenv import load_dotenv # Use the new OpenAI client
import random
import cohere 

load_dotenv()



cohere_api_key = os.getenv("COHERE_API_KEY")
cohere_client = cohere.Client(cohere_api_key)

app = FastAPI()


class ChatRequest(BaseModel):
    user_message: str

@app.post("/generate-response/")
async def generate_response(request: ChatRequest):
    try:
        response = cohere_client.generate(
            model = "command",
            prompt=f"You are a tourist who writes blogs. {request.user_message} Write a blog about it.",
            max_tokens=300,
            temperature=0.8,
            k=0,
            p=0.8,
            stop_sequences=["--"]
        )

        generated_text = response.generations[0].text
        
        try:
            url=os.getenv("UNPLASH_BASE_URL")
            headers = {
                "Authorization": f"Client-ID {os.getenv('UNPLASH_ACCESS_KEY')}"
            }
            
            params={
                "query": request.user_message,
                "per_page": random.randint(2, 4)
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
            "response":generated_text,
            "image_urls": image_urls
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Running
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
