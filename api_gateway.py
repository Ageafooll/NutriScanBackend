from fastapi import FastAPI
from pydantic import BaseModel
import requests
import json

app = FastAPI()

class ChatPrompt(BaseModel):
    prompt : str

class ImagePrompt(BaseModel):
    base64Image : str

@app.get("/")
def index():
    
    response = {"bruh":"bruh"}

    return response

@app.post("/chat")
def manage_chat_prompt(user_prompt: ChatPrompt):
    
    print(f"Got the chat user_prompt: {user_prompt.prompt}")

    URL = "http://llm_service:11434/api/chat"

    ai_payload = {
        "model": "llama3.2",

        "messages": [
            {
                "role": "system",
                "content": "You are a nutritionist. " \
                           "STRICTLY return the response with a JSON object with the key 'response'."
            },
            {
                "role": "user",
                "content": f"{user_prompt.prompt}."
            } 
        ],

        "stream": False,
        "format": {
            "type": "object",
            "properties":
            {
                "response":
                {
                    "type": "string",
                    "description": "Answer to users request"
                }
            },
            "required": ["response"]
        }
    }

    response = requests.post(URL, json=ai_payload).json()

    print(f"Got the chat response: {response}")

    chat_response = response["message"]["content"]

    try:
        final_output = json.loads(chat_response)
    except json.JSONDecodeError:
        return {"error":"Bu hıyar JSON göndermemiş"}

    return final_output

@app.post("/image")
def manage_image_prompt(user_prompt: ImagePrompt):
    
    print("Got the image in user_prompt")

    URL = "http://llm_service:11434/api/chat"

    ai_payload1 = {
        "model": "llava",

        "messages": [
            {
                "role": "system",
                "content": "You are a meal analyzer. Analyze the image and return the meal name and estimated weight in grams." 
            },
            {
                "role": "user",
                "content": "What meal is it and how many grams of it are there?",
                "images": [user_prompt.base64Image]
            } 
        ],
        "stream": False,

        "format": {
            "type": "object",
            "properties": 
            {
                "name": 
                {
                    "type": "string",
                    "description": "The name of the meal"
                },
                "gram": 
                {
                    "type": "integer",
                    "description": "The estimated weight in grams"
                }
            },
            "required": ["name", "gram"]
        }
    }

    response1 = requests.post(URL, json=ai_payload1).json()

    image_rec_output = response1["message"]["content"]

    print(f"Got the image recognition output: {image_rec_output}")

    try:
        food_in_image = json.loads(image_rec_output)
    except json.JSONDecodeError:
        return {"error":"Bu hıyar JSON göndermemiş"}

    ai_payload2 = {
        "model": "llama3.2",

        "messages": [
            {
                "role": "system",
                "content": "You are a nutritionist. Calculate the macros for the provided meal."
            },
            {
                "role": "user",
                "content": f"{food_in_image.get('gram')} grams of {food_in_image.get('name')}."
            } 
        ],

        "stream": False,
        "format": {
            "type": "object",
            "properties": 
            {
                "proteins": 
                {
                    "type": "integer",
                    "description": "Protein content in grams"
                },
                "carbohydrates": 
                {
                    "type": "integer",
                    "description": "Carbohydrate content in grams"
                },
                "fats": 
                {
                    "type": "integer",
                    "description": "Fat content in grams"
                }
            },
            "required": ["proteins", "carbohydrates", "fats"]
        }
    }

    response2 = requests.post(URL, json=ai_payload2).json()

    nutririon_output = response2["message"]["content"]

    print(f"Got the nutrition output: {nutririon_output}")

    try:
        nutrition_info = json.loads(nutririon_output)
    except json.JSONDecodeError:
        return {"error": "Bu herif json göndermemiş"}

    final_output = {**food_in_image, **nutrition_info}

    print(f"Got the final response: {final_output}")

    return final_output

