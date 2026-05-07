from fastapi import FastAPI, APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
import requests
import json
import pymysql

from database_logic import add_user, authenticate_user, remove_user
from jwt_logic import create_token, get_user_by_token

app = FastAPI()

#
# Kinds of payloads that our endpoints will accept
#
class ChatPrompt(BaseModel):
    prompt: str

class ImagePrompt(BaseModel):
    base64Image: str

class MealPrompt(BaseModel):
    name: str
    gram: int

class AuthenticationPayload(BaseModel):
    username: str
    password: str

class RemovePayload(BaseModel):
    username: str


@app.get("/deneme")
def deneme(current_user: dict = Depends(get_user_by_token)):
    
    response = {"bruh": "JWT calisiyor"}

    response.update(current_user)

    return response


#               ----------------------------------
#               Following endpoints are about LLMs
#               ----------------------------------

#
# Regular chat prompts are sent here
#
@app.post("/chat")
def manage_chat_prompt(user_prompt: ChatPrompt):
    
    print(f"Got the chat user_prompt: {user_prompt.prompt}")

    URL = "http://llm_service:11434/api/chat"

    ai_payload = {
        "model": "llama3.2",

        "messages": [
            {
                "role": "system",
                "content": "You are a nutritionist."
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
                    "description": "Answer to users prompt"
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
        return {"error":"JSON göndermemiş"}

    return final_output

#
# Image prompts are sent here to recieve nutrition information
#
@app.post("/mealimage")
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
        return {"error":"Dayi JSON göndermemiş"}

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
                "calories":
                {
                    "type": "integer",
                    "description": "Calories in kcal"
                },
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
            "required": ["calories", "proteins", "carbohydrates", "fats"]
        }
    }

    response = requests.post(URL, json=ai_payload2).json()

    nutririon_output = response["message"]["content"]

    print(f"Got the nutrition output: {nutririon_output}")

    try:
        nutrition_info = json.loads(nutririon_output)
    except json.JSONDecodeError:
        return {"error": "Bu herif json göndermemiş"}

    final_output = {**food_in_image, **nutrition_info}

    print(f"Got the final response: {final_output}")

    return final_output

#
# Meal information with no images are sent here to recieve nutrition information
#
@app.post("/mealnoimage")
def manage_meal_prompt(user_prompt: MealPrompt):
    
    URL = "http://llm_service:11434/api/chat"

    ai_payload = {
        "model": "llama3.2",

        "messages": [
            {
                "role": "system",
                "content": "You are a nutritionist. Calculate the macros for the provided meal."
            },
            {
                "role": "user",
                "content": f"{user_prompt.gram} grams of {user_prompt.name}."
            } 
        ],

        "stream": False,
        "format": {
            "type": "object",
            "properties": 
            {
                "calories":
                {
                    "type": "integer",
                    "description": "Calories in kcal"
                },
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
            "required": ["calories", "proteins", "carbohydrates", "fats"]
        }
    }

    response = requests.post(URL, json=ai_payload).json()

    nutririon_output = response["message"]["content"]

    print(f"Got the nutrition output: {nutririon_output}")

    try:
        final_output = json.loads(nutririon_output)
    except json.JSONDecodeError:
        return {"error": "Bu herif json göndermemiş"}

    print(f"Got the final response: {final_output}")

    return final_output


#           --------------------------------------
#           Following enpoints are about databases
#           --------------------------------------

#
# Username and passwords are sent here to create account
#
@app.post("/register")
def manage_register(payload: AuthenticationPayload):


    match add_user(payload.username, payload.password):
        case 1:
            return {"message": "Created user"}
        case 2:
            raise HTTPException(status_code=500, detail="Couldn't connecto to database")
        case 3:
            return {"message": f"User {payload.username} already exists"} 
        case 4:
            raise HTTPException(status_code=500, detail="Something wrong with the query")
        case _:
            return {"what":"what?"}
    


#
# Username and passwords are sent here for password authentication, and then you claim the token
#
@app.post("/login")
def manage_authentication(payload: AuthenticationPayload):

    #
    # First part is about password authentication, no tokens yet
    #

    auth_return = authenticate_user(payload.username, payload.password)

    match auth_return:
        case 1:
            print("What?")
        case 2:
            raise HTTPException(status_code=500, detail="Couldn't connecto to database")
        case 3:
            return {"message": "Username or password is wrong"} 
        case 4:
            raise HTTPException(status_code=500, detail="Something wrong with the query")
        case _:
            user_id = auth_return['user_id']
            is_premium = auth_return['is_premium']


    #
    # We will handle the token in this part
    #

    jwt_payload = {"sub": str(user_id), "is_premium": is_premium}

    users_token = create_token(jwt_payload)

    return {"message": "login successful", "access_token": users_token, "token_type": "bearer"}


@app.post("/removeuser")
def manage_authentication(payload: RemovePayload):


    match remove_user(payload.username):
        case 1:
            return {"message": "Successfully deleted the user"}
        case 2:
            raise HTTPException(status_code=500, detail="Couldn't connecto to database")
        case 3:
            return {"message": f"User {payload.username} doesn't exists"} 
        case 4:
            raise HTTPException(status_code=500, detail="Something wrong with the query")
        case _:
            return {"what":"what?"}
