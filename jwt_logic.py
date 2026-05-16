import os
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

#
#   General json web token logic is implemented here
# 

SECRET_KEY = os.getenv("SECRET_KEY", "hacklenmek_istiyorum_beni_hackleyin")
ALGORITHM ="HS256"
ACCESS_TOKEN_EXPIRE = 1440

#This tells the API we will use the bearer token part in header for authentication
security_scheme = HTTPBearer()


def create_token(data: dict):

    for_encoding = data.copy()

    expire_time = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE)

    for_encoding.update({"exp": expire_time})

    jwt_token = jwt.encode(for_encoding, SECRET_KEY, algorithm=ALGORITHM)

    return jwt_token


def get_user_by_token(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):


    try:
        token = credentials.credentials

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        user_id_str = payload.get("sub")
        user_id = int(user_id_str)
        is_premium = payload.get("is_premium")

        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Couldn't validate the token")

        return {"user_id": user_id, "is_premium": is_premium}
        
    except jwt.ExpiredSignatureError as e:
        print(e)
        raise HTTPException(status_code=401, detail="Token is expired")

    except jwt.InvalidTokenError as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Couldn't validate the token")
