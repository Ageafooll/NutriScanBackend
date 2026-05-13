from datetime import date
from typing import List
from fastapi import FastAPI, APIRouter, HTTPException, status, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
from time import sleep
import requests
import json
import pymysql
from schemas import ChatPrompt, FoodLogPayload, ImagePrompt, MealPrompt, AuthenticationPayload, ProfileUpdatePayload, UserRestrictionPayload, WaterLogPayload, WeightLogPayload

from jwt_logic import create_token, get_user_by_token
from database_logic import (
    DatabaseConnectionError, DatabaseError, DatabaseAlreadyExistsError, DatabaseNotFoundError,
    init_db,
    register_account, authenticate_account, delete_account,
    update_user_profile, get_user_profile,
    add_user_restriction, delete_user_restriction, get_user_restrictions,
    add_food_log, delete_food_log, get_food_logs,
    add_water_log, delete_water_log, get_water_logs, 
    add_weight_log, delete_weight_log, get_weight_logs
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)

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

@app.exception_handler(DatabaseError)
async def database_error_exception_handler(request: Request, exc: DatabaseError):
    return JSONResponse(
        status_code=500,
        content={"message": "An error occurred while processing your request. Please try again later."},
    )

@app.exception_handler(DatabaseConnectionError)
async def database_connection_error_handler(request: Request, exc: DatabaseConnectionError):
    return JSONResponse(
        status_code=500,
        content={"message": "Failed to connect to the database. Please try again later."},
    )

@app.exception_handler(DatabaseAlreadyExistsError)
async def database_already_exists_error_handler(request: Request, exc: DatabaseAlreadyExistsError):
    return JSONResponse(
        status_code=400,
        content={"message": "A record with this identifier already exists."},
    )

@app.exception_handler(DatabaseNotFoundError)
async def database_not_found_error_handler(request: Request, exc: DatabaseNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"message": "Record not found."},
    )

@app.post("/auth/register")
def manage_register(payload: AuthenticationPayload):
    register_account(payload)
    return {"message": "Account registered successfully"}

@app.post("/auth/login")
def manage_login(payload: AuthenticationPayload):
    # First part is about password authentication, no tokens yet
    auth_return = authenticate_account(payload)
    user_id = auth_return['user_id']
    is_premium = auth_return['has_premium']

    # We will handle the token in this part
    jwt_payload = {"sub": str(user_id), "is_premium": is_premium}
    users_token = create_token(jwt_payload)
    return {"message": "Login successful", "access_token": users_token, "token_type": "bearer"}

@app.delete("/users/me/remove")
def manage_remove_account(current_user: dict = Depends(get_user_by_token)):
    delete_account(current_user["user_id"])
    return {"message": "Account removed successfully"}

@app.post("/users/me/profile")
def manage_update_profile(payload: ProfileUpdatePayload, current_user: dict = Depends(get_user_by_token)):
    update_user_profile(current_user["user_id"], payload)
    return {"message": "Profile updated successfully"}

@app.get("/users/me/profile")
def manage_get_profile(current_user: dict = Depends(get_user_by_token)):
    return get_user_profile(current_user["user_id"])

@app.get("/users/me/restrictions")
def manage_get_restrictions(current_user: dict = Depends(get_user_by_token)):
    return get_user_restrictions(current_user["user_id"])

@app.post("/users/me/restrictions")
def manage_add_restrictions(payloads: List[UserRestrictionPayload], current_user: dict = Depends(get_user_by_token)):
    for payload in payloads:
        add_user_restriction(current_user["user_id"], payload)
    return {"message": "Restrictions added successfully"}

@app.delete("/users/me/restrictions/{restriction_id}")
def manage_delete_restriction(restriction_id: int, current_user: dict = Depends(get_user_by_token)):
    delete_user_restriction(restriction_id, current_user["user_id"])
    return {"message": "Restriction deleted successfully"}

@app.get("/logs/food")
def manage_get_food_logs(log_date: date = None, current_user: dict = Depends(get_user_by_token)):
    return get_food_logs(current_user["user_id"], log_date)

@app.post("/logs/food")
def manage_add_food_log(payload: FoodLogPayload, current_user: dict = Depends(get_user_by_token)):
    add_food_log(current_user["user_id"], payload)
    return {"message": "Food log added successfully"}

@app.delete("/logs/food/{foodlog_id}")
def manage_delete_food_log(foodlog_id: int, current_user: dict = Depends(get_user_by_token)):
    delete_food_log(foodlog_id, current_user["user_id"])
    return {"message": "Food log deleted successfully"}

@app.get("/logs/water")
def manage_get_water_logs(log_date: date = None, current_user: dict = Depends(get_user_by_token)):
    return get_water_logs(current_user["user_id"], log_date)

@app.post("/logs/water")
def manage_add_water_log(payload: WaterLogPayload, current_user: dict = Depends(get_user_by_token)):
    add_water_log(current_user["user_id"], payload)
    return {"message": "Water log added successfully"}

@app.delete("/logs/water/{waterlog_id}")
def manage_delete_water_log(waterlog_id: int, current_user: dict = Depends(get_user_by_token)):
    delete_water_log(waterlog_id, current_user["user_id"])
    return {"message": "Water log deleted successfully"}

@app.get("/logs/weight")
def manage_get_weight_logs(log_date: date = None, current_user: dict = Depends(get_user_by_token)):
    return get_weight_logs(current_user["user_id"], log_date)

@app.post("/logs/weight")
def manage_add_weight_log(payload: WeightLogPayload, current_user: dict = Depends(get_user_by_token)):
    add_weight_log(current_user["user_id"], payload)
    return {"message": "Weight log added successfully"}

@app.delete("/logs/weight/{weightlog_id}")
def manage_delete_weight_log(weightlog_id: int, current_user: dict = Depends(get_user_by_token)):
    delete_weight_log(weightlog_id, current_user["user_id"])
    return {"message": "Weight log deleted successfully"}
