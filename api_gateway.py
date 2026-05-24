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

from jwt_logic import create_token, get_user_by_token
from ai_logic import send_chat_prompt, send_meal_prompt, send_image_prompt, send_diet_prompt

from schemas import (
    ChatPrompt, DietMealPayload, DietProgramPayload, DietPrompt, FoodLogPayload, ImagePrompt, MealPrompt, 
    AuthenticationPayload, ProfileUpdatePayload, UserRestrictionPayload, 
    WaterLogPayload, WeightLogPayload
) 

from database import (
    DatabaseConnectionError, DatabaseError, DatabaseAlreadyExistsError, DatabaseNotFoundError,
    init_db,
    register_account, authenticate_account, delete_account,
    upgrade_to_premium, downgrade_from_premium,
    update_user_profile, get_user_profile,
    add_user_restriction, delete_user_restriction, get_user_restrictions,
    add_food_log, delete_food_log, get_food_logs,
    add_water_log, delete_water_log, get_water_logs, 
    add_weight_log, delete_weight_log, get_weight_logs,
    create_diet_program, delete_diet_program, get_user_diet_programs,
    add_diet_meal, delete_diet_meal, get_diet_meals,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)

# ===== Error Handlers =====

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

# ==== Helper Functions =====
def require_premium(current_user: dict = Depends(get_user_by_token)):
    if not current_user.get("is_premium"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This feature requires a premium subscription."
        )
        
    return current_user

# ===== Health and Debug =====
@app.get("/health", tags=["Debug"])
def health_check():
    return {"status": "ok"}

@app.get("/test/jwt", tags=["Debug"])
def test_jwt(current_user: dict = Depends(get_user_by_token)):
    response = {"message": "JWT is working"}
    response.update(current_user)
    return response

@app.get("/test/premium", tags=["Debug"])
def test_premium(current_user: dict = Depends(require_premium)):
    return {"message": "User is premium"}

@app.post("/test/premium/upgrade", tags=["Debug"])
def manage_upgrade_premium(current_user: dict = Depends(get_user_by_token)):
    # This is a debug endpoint to make a user premium
    upgrade_to_premium(current_user["user_id"])
    return {"message": "User made premium"}

@app.post("/test/premium/downgrade", tags=["Debug"])
def manage_downgrade_premium(current_user: dict = Depends(get_user_by_token)):
    # This is a debug endpoint to make a user not premium
    downgrade_from_premium(current_user["user_id"])
    return {"message": "User downgraded from premium"}

# ===== Authentication =====
@app.post("/auth/register", tags=["Authentication"])
def manage_register(payload: AuthenticationPayload):
    register_account(payload)
    return {"message": "Account registered successfully"}

@app.post("/auth/login", tags=["Authentication"])
def manage_login(payload: AuthenticationPayload):
    # First part is about password authentication, no tokens yet
    auth_return = authenticate_account(payload)

    if(auth_return):
        user_id = auth_return['user_id']
        is_premium = auth_return['has_premium']
    else:
        return {"message": "Mail or password is wrong"}

    # We will handle the token in this part
    jwt_payload = {"sub": str(user_id), "is_premium": is_premium}
    users_token = create_token(jwt_payload)
    return {"message": "Login successful", "access_token": users_token, "token_type": "bearer"}

# ===== User Account and Profile =====
@app.delete("/users/me/remove", tags=["Users"])
def manage_remove_account(current_user: dict = Depends(get_user_by_token)):
    delete_account(current_user["user_id"])
    return {"message": "Account removed successfully"}

@app.post("/users/me/premium", tags=["Users"])
def manage_upgrade_to_premium(current_user: dict = Depends(get_user_by_token)):
    upgrade_to_premium(current_user["user_id"])
    jwt_payload = {"sub": str(current_user["user_id"]), "is_premium": 1}
    new_token = create_token(jwt_payload)
    return {"message": "Account upgraded to premium", "access_token": new_token, "token_type": "bearer"}

@app.delete("/users/me/premium", tags=["Users"])
def manage_downgrade_from_premium(current_user: dict = Depends(get_user_by_token)):
    downgrade_from_premium(current_user["user_id"])
    jwt_payload = {"sub": str(current_user["user_id"]), "is_premium": 0}
    new_token = create_token(jwt_payload)
    return {"message": "Premium subscription cancelled", "access_token": new_token, "token_type": "bearer"}

@app.post("/users/me/profile", tags=["Users"])
def manage_update_profile(payload: ProfileUpdatePayload, current_user: dict = Depends(get_user_by_token)):
    update_user_profile(current_user["user_id"], payload)
    return {"message": "Profile updated successfully"}

@app.get("/users/me/profile", tags=["Users"])
def manage_get_profile(current_user: dict = Depends(get_user_by_token)):
    return get_user_profile(current_user["user_id"])

# ===== User Restrictions =====
@app.get("/users/me/restrictions", tags=["Users"])
def manage_get_restrictions(current_user: dict = Depends(get_user_by_token)):
    return get_user_restrictions(current_user["user_id"])

@app.post("/users/me/restrictions", tags=["Users"])
def manage_add_restrictions(payloads: List[UserRestrictionPayload], current_user: dict = Depends(get_user_by_token)):
    for payload in payloads:
        add_user_restriction(current_user["user_id"], payload)
    return {"message": "Restrictions added successfully"}

@app.delete("/users/me/restrictions/{restriction_id}", tags=["Users"])
def manage_delete_restriction(restriction_id: int, current_user: dict = Depends(get_user_by_token)):
    delete_user_restriction(restriction_id, current_user["user_id"])
    return {"message": "Restriction deleted successfully"}

# ===== Food Logs =====
@app.get("/logs/food", tags=["Food Logs"])
def manage_get_food_logs(log_date: date = None, current_user: dict = Depends(get_user_by_token)):
    return get_food_logs(current_user["user_id"], log_date)

@app.post("/logs/food", tags=["Food Logs"])
def manage_add_food_log(payload: FoodLogPayload, current_user: dict = Depends(get_user_by_token)):
    add_food_log(current_user["user_id"], payload)
    return {"message": "Food log added successfully"}

@app.delete("/logs/food/{foodlog_id}", tags=["Food Logs"])
def manage_delete_food_log(foodlog_id: int, current_user: dict = Depends(get_user_by_token)):
    delete_food_log(foodlog_id, current_user["user_id"])
    return {"message": "Food log deleted successfully"}

# ===== Water Logs =====
@app.get("/logs/water", tags=["Water Logs"])
def manage_get_water_logs(log_date: date = None, current_user: dict = Depends(get_user_by_token)):
    return get_water_logs(current_user["user_id"], log_date)

@app.post("/logs/water", tags=["Water Logs"])
def manage_add_water_log(payload: WaterLogPayload, current_user: dict = Depends(get_user_by_token)):
    add_water_log(current_user["user_id"], payload)
    return {"message": "Water log added successfully"}

@app.delete("/logs/water/{waterlog_id}", tags=["Water Logs"])
def manage_delete_water_log(waterlog_id: int, current_user: dict = Depends(get_user_by_token)):
    delete_water_log(waterlog_id, current_user["user_id"])
    return {"message": "Water log deleted successfully"}

# ===== Weight Logs =====
@app.get("/logs/weight", tags=["Weight Logs"])
def manage_get_weight_logs(log_date: date = None, current_user: dict = Depends(get_user_by_token)):
    return get_weight_logs(current_user["user_id"], log_date)

@app.post("/logs/weight", tags=["Weight Logs"])
def manage_add_weight_log(payload: WeightLogPayload, current_user: dict = Depends(get_user_by_token)):
    add_weight_log(current_user["user_id"], payload)
    return {"message": "Weight log added successfully"}

@app.delete("/logs/weight/{weightlog_id}", tags=["Weight Logs"])
def manage_delete_weight_log(weightlog_id: int, current_user: dict = Depends(get_user_by_token)):
    delete_weight_log(weightlog_id, current_user["user_id"])
    return {"message": "Weight log deleted successfully"}

# ===== Diet Program Management =====
@app.get("/diet/programs", tags=["Diet Programs"])
def manage_get_diet_programs(current_user: dict = Depends(get_user_by_token)):
    return get_user_diet_programs(current_user["user_id"])

@app.post("/diet/programs", tags=["Diet Programs"])
def manage_create_diet_program(payload: DietProgramPayload, current_user: dict = Depends(require_premium)):
    create_diet_program(current_user["user_id"], payload)
    return {"message": "Diet program created successfully"}

@app.delete("/diet/programs/{diet_id}", tags=["Diet Programs"])
def manage_delete_diet_program(diet_id: int, current_user: dict = Depends(get_user_by_token)):
    delete_diet_program(diet_id, current_user["user_id"])
    return {"message": "Diet program deleted successfully"}

@app.get("/diet/{diet_id}/meals", tags=["Diet Programs"])
def manage_get_diet_meals(diet_id: int, current_user: dict = Depends(get_user_by_token)):
    return get_diet_meals(diet_id, current_user["user_id"])

@app.post("/diet/{diet_id}/meals", tags=["Diet Programs"])
def manage_add_diet_meal(diet_id: int, payload: DietMealPayload, current_user: dict = Depends(get_user_by_token)):
    add_diet_meal(diet_id, payload, current_user["user_id"])
    return {"message": "Diet meal added successfully"}

@app.delete("/diet/{diet_id}/meals/{meal_id}", tags=["Diet Programs"])
def manage_delete_diet_meal(diet_id: int, meal_id: int, current_user: dict = Depends(get_user_by_token)):
    delete_diet_meal(meal_id, diet_id, current_user["user_id"])
    return {"message": "Diet meal deleted successfully"}

# ===== AI Endpoints =====
@app.post("/ai/chat", tags=["AI"])
def manage_chat_prompt(user_prompt: ChatPrompt, current_user: dict = Depends(get_user_by_token)):

    final_response = send_chat_prompt(user_prompt.prompt)

    if (final_response == -1):
        raise HTTPException(status_code=500, detail="AI made a mistake")
    else:
        return final_response


@app.post("/ai/mealnoimage", tags=["AI"])
def manage_meal_prompt(user_prompt: MealPrompt, current_user: dict = Depends(get_user_by_token)):

    final_response = send_meal_prompt(user_prompt.gram, user_prompt.name)

    if (final_response == -1):
        raise HTTPException(status_code=500, detail="AI made a mistake")
    else:
        return final_response


@app.post("/ai/mealimage", tags=["AI"])
def manage_image_prompt(user_prompt: ImagePrompt, current_user: dict = Depends(get_user_by_token)):

    final_response = send_image_prompt(user_prompt.base64Image)

    if (final_response == -1):
        raise HTTPException(status_code=500, detail="AI made a mistake")
    else:
        return final_response


@app.post("/ai/diet", tags=["AI"])
def manage_diet_prompt(user_prompt: DietPrompt, current_user: dict = Depends(require_premium)):

    # We will get the restrictions of the user and send them to the AI to consider in the diet plan
    restrictions = get_user_restrictions(current_user["user_id"])

    final_response = send_diet_prompt(user_prompt.goal, restrictions)

    if (final_response == -1):
        raise HTTPException(status_code=500, detail="AI made a mistake")
    else:
        return final_response
