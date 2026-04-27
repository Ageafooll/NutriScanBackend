from fastapi import FastAPI, APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
import requests
import json
import pymysql
from passlib.context import CryptContext

from jwt_logic import create_token, get_user_by_token

app = FastAPI()

#
# Kinds of payloads that our endpoints will accept
#
class ChatPrompt(BaseModel):
    prompt : str

class ImagePrompt(BaseModel):
    base64Image : str

class MealPrompt(BaseModel):
    name : str
    gram : int

class AuthenticationPayload(BaseModel):
    username : str
    password : str


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

    #We hash and salt the password 
    crypt_context = CryptContext(
        schemes=["argon2"],
        default="argon2",
        deprecated="auto",
    )

    hashed_salted_pw = crypt_context.hash(payload.password)


    try:
        connection = pymysql.connect(
            host="db_service",
            user="python_api",
            password="1234",
            database="users_db",
            port=3306,
            cursorclass=pymysql.cursors.DictCursor
        )        
    except pymysql.Error as e:
        printf(f"Niye baglanamadi? {e}")


    init_sql = '''CREATE TABLE IF NOT EXISTS users (
             user_id INT AUTO_INCREMENT PRIMARY KEY,
             username VARCHAR(30) UNIQUE,
             password VARCHAR(255),
             is_premium INT,
             active INT) AUTO_INCREMENT = 1000; '''
    
    check_sql = "SELECT username FROM users WHERE username=%s;"
             
    insert_sql = "INSERT INTO users (username, password, is_premium, active) VALUES (%s, %s, 0, 1);"
             

    try:
        with connection.cursor() as cursor:

            cursor.execute(init_sql)

            cursor.execute(check_sql, (payload.username))

            if(cursor.rowcount != 0):
                print(f"User {payload.username} already exists")
                return {"message": f"User {payload.username} already exists"}            

            cursor.execute(insert_sql, (payload.username, hashed_salted_pw))

            connection.commit()
            print(f"created the user {payload.username}")

    except pymysql.Error as e:
        print(f"query'de hata {e}")
        return {"message": "Olmadi dayi"}

    finally:
        connection.close()

    return {"message": "Created user"}


#
# Username and passwords are sent here for password authentication
#
@app.post("/login")
def manage_authentication(payload: AuthenticationPayload):

    #
    # First part is about password authentication, no tokens yet
    #

    crypt_context = CryptContext(
        schemes=["argon2"],
        default="argon2",
        deprecated="auto",
    )


    try:
        connection = pymysql.connect(
            host="db_service",
            user="python_api",
            password="1234",
            database="users_db",
            port=3306,
            cursorclass=pymysql.cursors.DictCursor
        )        
    except pymysql.Error as e:
        printf(f"Niye baglanamadi? {e}")

    auth_sql = "SELECT password FROM users WHERE username=%s;"
    info_sql = "SELECT user_id, is_premium FROM users WHERE username=%s;"

    try:
        with connection.cursor() as cursor:

            cursor.execute(auth_sql,(payload.username,))

            if(cursor.rowcount == 0):
                print(f"User {payload.username} doesn't exists")
                return {"message": "Username or password is wrong"}            


            result = cursor.fetchone()

            if(crypt_context.verify(payload.password, result["password"])):

                print(f"Password auth was successful for {payload.username}")

                cursor.execute(info_sql,(payload.username,))

                result = cursor.fetchone()

                user_id = result["user_id"]
                is_premium = result["is_premium"]
            
            else:
                return {"message": "Username or password is wrong"}
            

    except pymysql.Error as e:
        print(f"query'de hata {e}")
        return {"message": "Olmadi dayi"}

    finally:
        connection.close()


    #
    # We will handle the token in this part
    #

    jwt_payload = {"sub": str(user_id), "is_premium": is_premium}

    users_token = create_token(jwt_payload)

    return {"message": "login successful", "access_token": users_token, "token_type": "bearer"}


    
