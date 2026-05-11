import requests
import json

#
# AI requests are structured and sent here
#

#Change the URL and MODEL if you decide to change to something like gemini vision
URL = "http://llm_service:11434/api/chat"
MODEL = "llama3.2"


#
# Sending regular chat prompt to AI
#
def send_chat_prompt(prompt: str):

    ai_payload = {
        "model": MODEL,

        "messages": [
            {
                "role": "system",
                "content": "You are a nutritionist."
            },
            {
                "role": "user",
                "content": f"{prompt}."
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

    try:
        response = requests.post(URL, json=ai_payload).json()
    except requests.exceptions.RequestException as e:
        print(f"The problem is {e}")

    print(f"Got the chat response: {response}")

    chat_response = response["message"]["content"]

    try:
        final_output = json.loads(chat_response)
    except json.JSONDecodeError:
        print("AI returned the wrong structure")
        return -1

    return final_output


#
# Sends meal prompt with no image
#
def send_meal_prompt(gram: int, name: str):
    
    ai_payload = {
        "model": MODEL,

        "messages": [
            {
                "role": "system",
                "content": "You are a nutritionist. Calculate the macros for the provided meal."
            },
            {
                "role": "user",
                "content": f"{gram} grams of {name}."
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
        print("AI returned the wrong structure")
        return -1

    print(f"Got the final response: {final_output}")

    return final_output


#
# Sending Image prompt to image recognition then its response to regular Gen AI
#
def send_image_prompt(base64Image: str):


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
                "images": [base64Image]
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

    try:
        response1 = requests.post(URL, json=ai_payload1).json()
    except requests.exceptions.RequestException as e:
        print(f"The problem is {e}")

    image_rec_output = response1["message"]["content"]

    print(f"Got the image recognition output: {image_rec_output}")

    try:
        food_in_image = json.loads(image_rec_output)
        gram = food_in_image.get('gram')
        food_name = food_in_image.get('name')
    except json.JSONDecodeError:
        print("AI returned the wrong structure")
        return -1
    

    nutrition_output = send_meal_prompt(gram, food_name)

    final_output = {**food_in_image, **nutrition_output}

    print(f"Got the final response: {final_output}")

    return final_output


#
# Sending goal to get a diet plan accordingly
#
def send_diet_prompt(goal: str):

    #Lütfen sövmeyin
    ai_payload = {
        "model": MODEL,

        "messages": [
            {
                "role": "system",
                "content": "You are a nutritionist. Send a 7 days of meal diet plan according to users goal. Send meal names and macros"
            },
            {
                "role": "user",
                "content": f"Users goal is {goal}."
            } 
        ],

        "stream": False,
        "format": {
            "type": "object",

            "properties": 
            {
                "sunday": 
                {
                    "type": "object",
                    "properties": 
                    {
                        "name": 
                        {
                            "type": "string",
                            "description": "Name of the meal"
                        },
                        "gram": 
                        {
                            "type": "integer",
                            "description": "Meals weight in gram"
                        },
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
                    "required": ["name", "gram", "calories", "proteins", "carbohydrates", "fats"]
                },

                "monday": 
                {
                    "type": "object",
                    "properties": 
                    {
                        "name": 
                        {
                            "type": "string",
                            "description": "Name of the meal"
                        },
                        "gram": 
                        {
                            "type": "integer",
                            "description": "Meals weight in gram"
                        },
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
                    "required": ["name", "gram", "calories", "proteins", "carbohydrates", "fats"]
                },

                "tuesday": 
                {
                    "type": "object",
                    "properties": 
                    {
                        "name": 
                        {
                            "type": "string",
                            "description": "Name of the meal"
                        },
                        "gram": 
                        {
                            "type": "integer",
                            "description": "Meals weight in gram"
                        },
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
                    "required": ["name", "gram", "calories", "proteins", "carbohydrates", "fats"]
                },

                "wednesday": 
                {
                    "type": "object",
                    "properties": 
                    {
                        "name": 
                        {
                            "type": "string",
                            "description": "Name of the meal"
                        },
                        "gram": 
                        {
                            "type": "integer",
                            "description": "Meals weight in gram"
                        },
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
                    "required": ["name", "gram", "calories", "proteins", "carbohydrates", "fats"]
                },

                "thursday": 
                {
                    "type": "object",
                    "properties": 
                    {
                        "name": 
                        {
                            "type": "string",
                            "description": "Name of the meal"
                        },
                        "gram": 
                        {
                            "type": "integer",
                            "description": "Meals weight in gram"
                        },
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
                    "required": ["name", "gram", "calories", "proteins", "carbohydrates", "fats"]
                },

                "friday": 
                {
                    "type": "object",
                    "properties": 
                    {
                        "name": 
                        {
                            "type": "string",
                            "description": "Name of the meal"
                        },
                        "gram": 
                        {
                            "type": "integer",
                            "description": "Meals weight in gram"
                        },
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
                    "required": ["name", "gram", "calories", "proteins", "carbohydrates", "fats"]
                },

                "saturday": 
                {
                    "type": "object",
                    "properties": 
                    {
                        "name": 
                        {
                            "type": "string",
                            "description": "Name of the meal"
                        },
                        "gram": 
                        {
                            "type": "integer",
                            "description": "Meals weight in gram"
                        },
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
                    "required": ["name", "gram", "calories", "proteins", "carbohydrates", "fats"]
                }

            },

            "required": ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
        }
    }

    response = requests.post(URL, json=ai_payload).json()

    diet_output = response["message"]["content"]

    print(f"Got the diet output: {diet_output}")

    try:
        final_output = json.loads(diet_output)
    except json.JSONDecodeError:
        print("AI returned the wrong structure")
        return -1

    print(f"Got the final response: {final_output}")

    return final_output