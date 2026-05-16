from fastapi import FastAPI, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Optional
import requests
import json

from database_logic import (
    add_user, authenticate_user, remove_user,
    save_meal, get_meal_history,
    get_user_profile, update_user_profile,
)
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

class ProfileUpdate(BaseModel):
    weight:             Optional[float] = Field(None, description="Current weight in kg")
    goal_weight:        Optional[float] = Field(None, description="Target weight in kg")
    daily_calorie_goal: Optional[int]   = Field(None, description="Daily calorie goal in kcal")


# ---------------------------------------------------------------------------
#   Debug / health
# ---------------------------------------------------------------------------

@app.get("/deneme")
def deneme(current_user: dict = Depends(get_user_by_token)):
    response = {"bruh": "JWT calisiyor"}
    response.update(current_user)
    return response


# ---------------------------------------------------------------------------
#   LLM endpoints
# ---------------------------------------------------------------------------

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
            "properties": {
                "response": {
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
        return {"error": "JSON göndermemiş"}

    return final_output


#
# Image prompts are sent here to receive nutrition information.
# Requires JWT — the meal is automatically saved to the user's history.
#
@app.post("/mealimage")
def manage_image_prompt(
    user_prompt: ImagePrompt,
    current_user: dict = Depends(get_user_by_token)
):
    print("Got the image in user_prompt")

    URL = "http://llm_service:11434/api/chat"

    # --- Step 1: identify the meal via LLaVA ---
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
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the meal"
                },
                "gram": {
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
        return {"error": "Dayi JSON göndermemiş"}

    # --- Step 2: calculate macros via Llama ---
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
            "properties": {
                "calories":      {"type": "integer", "description": "Calories in kcal"},
                "proteins":      {"type": "integer", "description": "Protein content in grams"},
                "carbohydrates": {"type": "integer", "description": "Carbohydrate content in grams"},
                "fats":          {"type": "integer", "description": "Fat content in grams"}
            },
            "required": ["calories", "proteins", "carbohydrates", "fats"]
        }
    }

    response2 = requests.post(URL, json=ai_payload2).json()
    nutrition_output = response2["message"]["content"]
    print(f"Got the nutrition output: {nutrition_output}")

    try:
        nutrition_info = json.loads(nutrition_output)
    except json.JSONDecodeError:
        return {"error": "Bu herif json göndermemiş"}

    final_output = {**food_in_image, **nutrition_info}
    print(f"Got the final response: {final_output}")

    # --- Step 3: persist the meal ---
    save_result = save_meal(current_user["user_id"], final_output)
    if save_result != 1:
        print(f"Warning: could not save meal for user {current_user['user_id']} (code {save_result})")

    return final_output


#
# Meal information with no images are sent here to receive nutrition information.
# Requires JWT — the meal is automatically saved to the user's history.
#
@app.post("/mealnoimage")
def manage_meal_prompt(
    user_prompt: MealPrompt,
    current_user: dict = Depends(get_user_by_token)
):
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
            "properties": {
                "calories":      {"type": "integer", "description": "Calories in kcal"},
                "proteins":      {"type": "integer", "description": "Protein content in grams"},
                "carbohydrates": {"type": "integer", "description": "Carbohydrate content in grams"},
                "fats":          {"type": "integer", "description": "Fat content in grams"}
            },
            "required": ["calories", "proteins", "carbohydrates", "fats"]
        }
    }

    response = requests.post(URL, json=ai_payload).json()
    nutrition_output = response["message"]["content"]
    print(f"Got the nutrition output: {nutrition_output}")

    try:
        nutrition_info = json.loads(nutrition_output)
    except json.JSONDecodeError:
        return {"error": "Bu herif json göndermemiş"}

    final_output = {
        "name": user_prompt.name,
        "gram": user_prompt.gram,
        **nutrition_info
    }
    print(f"Got the final response: {final_output}")

    # Persist the meal
    save_result = save_meal(current_user["user_id"], final_output)
    if save_result != 1:
        print(f"Warning: could not save meal for user {current_user['user_id']} (code {save_result})")

    return final_output


# ---------------------------------------------------------------------------
#   Database / auth endpoints
# ---------------------------------------------------------------------------

#
# Username and passwords are sent here to create account
#
@app.post("/register")
def manage_register(payload: AuthenticationPayload):

    match add_user(payload.username, payload.password):
        case 1:
            return {"message": "Created user"}
        case 2:
            raise HTTPException(status_code=500, detail="Couldn't connect to database")
        case 3:
            return {"message": f"User {payload.username} already exists"}
        case 4:
            raise HTTPException(status_code=500, detail="Something wrong with the query")
        case _:
            return {"what": "what?"}


#
# Username and passwords are sent here for password authentication, then you claim the token
#
@app.post("/login")
def manage_authentication(payload: AuthenticationPayload):

    auth_return = authenticate_user(payload.username, payload.password)

    match auth_return:
        case 1:
            print("What?")
        case 2:
            raise HTTPException(status_code=500, detail="Couldn't connect to database")
        case 3:
            return {"message": "Username or password is wrong"}
        case 4:
            raise HTTPException(status_code=500, detail="Something wrong with the query")
        case _:
            user_id    = auth_return["user_id"]
            is_premium = auth_return["is_premium"]

    jwt_payload  = {"sub": str(user_id), "is_premium": is_premium}
    users_token  = create_token(jwt_payload)

    return {"message": "login successful", "access_token": users_token, "token_type": "bearer"}


@app.post("/removeuser")
def manage_remove_user(payload: RemovePayload):

    match remove_user(payload.username):
        case 1:
            return {"message": "Successfully deleted the user"}
        case 2:
            raise HTTPException(status_code=500, detail="Couldn't connect to database")
        case 3:
            return {"message": f"User {payload.username} doesn't exist"}
        case 4:
            raise HTTPException(status_code=500, detail="Something wrong with the query")
        case _:
            return {"what": "what?"}


# ---------------------------------------------------------------------------
#   Meal history endpoints
# ---------------------------------------------------------------------------

@app.get("/history")
def get_history(current_user: dict = Depends(get_user_by_token)):
    """Returns all saved meals for the authenticated user, newest first."""

    meals = get_meal_history(current_user["user_id"])
    return {"user_id": current_user["user_id"], "meals": meals}


# ---------------------------------------------------------------------------
#   User profile endpoints
# ---------------------------------------------------------------------------

@app.get("/profile")
def get_profile(current_user: dict = Depends(get_user_by_token)):
    """Returns the authenticated user's weight, goal weight, and daily calorie goal."""

    profile = get_user_profile(current_user["user_id"])

    if profile is None:
        raise HTTPException(status_code=500, detail="Could not retrieve profile")

    return {"user_id": current_user["user_id"], **profile}


@app.put("/profile")
def update_profile(
    payload: ProfileUpdate,
    current_user: dict = Depends(get_user_by_token)
):
    """Updates weight, goal_weight, and/or daily_calorie_goal for the authenticated user."""

    result = update_user_profile(current_user["user_id"], payload.model_dump())

    match result:
        case 1:
            return {"message": "Profile updated successfully"}
        case 2:
            raise HTTPException(status_code=500, detail="Couldn't connect to database")
        case 4:
            raise HTTPException(status_code=500, detail="Something wrong with the query")
        case _:
            return {"message": "Profile updated successfully"}
