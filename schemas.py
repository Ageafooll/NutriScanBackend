from pydantic import BaseModel
from typing import Dict, Optional
from datetime import date

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
    mail: str
    password: str

class ProfileUpdatePayload(BaseModel):
    mail: str

class ProfileUpdatePayload(BaseModel):
    name: str
    sex: str
    birth_date: date
    height: int
    weight: int
    target_weight: int
    activity_level: str # SEDENTARY, LIGHTLY_ACTIVE, ACTIVE, VERY_ACTIVE
    goal_type: str # LOSE_WEIGHT, MAINTAIN_WEIGHT, GAIN_WEIGHT, GAIN_MUSCLE

class UserRestrictionPayload(BaseModel):
    restriction_type: str
    restriction_value: str

class FoodLogPayload(BaseModel):
    name: str
    calories: int
    carbohydrates: float
    proteins: float
    fats: float
    micronutrients: Optional[Dict[str, float]] = {}
    serving_size: int
    meal_type: str # BREAKFAST, LUNCH, DINNER, SNACK
    log_date: date

class WaterLogPayload(BaseModel):
    amount: int # ml
    log_date: date

class WeightLogPayload(BaseModel):
    weight: int # kg
    log_date: date