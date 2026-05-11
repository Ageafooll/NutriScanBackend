from fastapi import FastAPI, APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
import requests
import json
import pymysql

from ai_logic import send_chat_prompt, send_meal_prompt, send_image_prompt
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

    final_response = send_chat_prompt(user_prompt.prompt)

    if (final_response == -1):
        raise HTTPException(status_code=500, detail="AI made a mistake")
    else:
        return final_response



#
# Meal information with no images are sent here to recieve nutrition information
#
@app.post("/mealnoimage")
def manage_meal_prompt(user_prompt: MealPrompt):
    
    print(f"Got the meal prompt: {user_prompt.gram} of {user_prompt.name}")

    final_response = send_meal_prompt(user_prompt.gram, user_prompt.name)

    if (final_response == -1):
        raise HTTPException(status_code=500, detail="AI made a mistake")
    else:
        return final_response



#
# Image prompts are sent here to recieve nutrition information
#
@app.post("/mealimage")
def manage_image_prompt(user_prompt: ImagePrompt):
    
    print("Got the image in user_prompt")

    final_response = send_image_prompt(user_prompt.base64Image)

    if (final_response == -1):
        raise HTTPException(status_code=500, detail="AI made a mistake")
    else:
        return final_response




#           --------------------------------------
#           Following enpoints are about user management
#           --------------------------------------

#
# Username and passwords are sent here to create account
#
@app.post("/register")
def manage_register(payload: AuthenticationPayload):


    match add_user(payload.username, payload.password):
        case 1:
            return {"message": "Created user"}
        case -1:
            raise HTTPException(status_code=500, detail="Couldn't connecto to database")
        case -2:
            return {"message": f"User {payload.username} already exists"} 
        case -3:
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
        case -1:
            raise HTTPException(status_code=500, detail="Couldn't connecto to database")
        case -2:
            return {"message": "Username or password is wrong"} 
        case -3:
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



#
# Username is sent here to remove account
#
@app.post("/removeuser")
def manage_authentication(payload: RemovePayload):


    match remove_user(payload.username):
        case 1:
            return {"message": "Successfully deleted the user"}
        case -1:
            raise HTTPException(status_code=500, detail="Couldn't connecto to database")
        case -2:
            return {"message": f"User {payload.username} doesn't exists"} 
        case -3:
            raise HTTPException(status_code=500, detail="Something wrong with the query")
        case _:
            return {"what":"what?"}
