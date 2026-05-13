import pymysql
from passlib.context import CryptContext
from datetime import date
from time import sleep
from functools import wraps
import json
from schemas import AuthenticationPayload, ProfileUpdatePayload, FoodLogPayload, UserRestrictionPayload, WaterLogPayload, WeightLogPayload

#DB variables
HOST = "db_service"
USER = "python_api"
PASSWORD = "1234"
DATABASE = "users_db"
PORT = 3306

#Hashing algorithm we will use
crypt_context = CryptContext(
        schemes=["argon2"],
        default="argon2",
        deprecated="auto",
    )

#
#   Database connections and queries implemented here
#

SCHEMA = """
    CREATE TABLE IF NOT EXISTS users (
        user_id INT AUTO_INCREMENT PRIMARY KEY,
        mail VARCHAR(255) UNIQUE,
        password VARCHAR(255),
        has_premium BOOLEAN DEFAULT FALSE
    );

    CREATE TABLE IF NOT EXISTS user_profiles (
        profile_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        name VARCHAR(30),
        sex VARCHAR(10), -- MALE, FEMALE, OTHER
        birth_date DATE,
        height INT, -- cm
        weight INT, -- kg
        target_weight INT, -- kg
        activity_level VARCHAR(20), -- SEDENTARY, LIGHTLY_ACTIVE, ACTIVE, VERY_ACTIVE
        goal_type VARCHAR(20), -- LOSE_WEIGHT, MAINTAIN_WEIGHT, GAIN_WEIGHT, GAIN_MUSCLE

        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS user_restrictions (
        restriction_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        restriction_type VARCHAR(20), -- ALLERGY, PREFERENCE
        restriction_value VARCHAR(255),

        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS foodlogs (
        foodlog_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        food_name VARCHAR(255),
        calories INT,
        protein INT,
        carbs INT,
        fat INT,
        micros JSON,
        serving_size INT,
        meal_type VARCHAR(20), -- BREAKFAST, LUNCH, DINNER, SNACK
        date DATE,
        log_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS waterlogs (
        waterlog_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        amount INT, -- ml
        date DATE,
        log_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS weightlogs (
        weightlog_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        weight INT, -- kg
        date DATE,
        log_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS diet_program (
        diet_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        start_date DATE,
        end_date DATE,
        target_calories INT,
        target_protein INT,
        target_carbs INT,
        target_fat INT,
        goal_type VARCHAR(20) -- LOSE_WEIGHT, MAINTAIN_WEIGHT, GAIN_WEIGHT, GAIN_MUSCLE
    );

    CREATE TABLE IF NOT EXISTS diet_meals (
        meal_id INT AUTO_INCREMENT PRIMARY KEY,
        diet_id INT,
        meal_name VARCHAR(255),
        calories INT,
        protein INT, 
        carbs INT,
        fat INT,
        micros JSON,
        serving_size INT,
        meal_type VARCHAR(20), -- BREAKFAST, LUNCH, DINNER, SNACK
        date DATE,

        FOREIGN KEY (diet_id) REFERENCES diet_program(diet_id) ON DELETE CASCADE
    );
"""


# Error Handling

class DatabaseError(Exception): pass
class DatabaseConnectionError(Exception): pass
class DatabaseAlreadyExistsError(DatabaseError): pass
class DatabaseNotFoundError(DatabaseError): pass

def get_connection():
    retries = 10
    while retries > 0:
        try:
            connection = pymysql.connect(
                host=HOST,
                user=USER,
                password=PASSWORD,
                database=DATABASE,
                port=PORT,
                cursorclass=pymysql.cursors.DictCursor,
                client_flag=pymysql.constants.CLIENT.MULTI_STATEMENTS
            )
            return connection

        except pymysql.Error as e:
            print(f"Database connection failed: {e}. Retrying in 5 seconds...")
            sleep(5)
            retries -= 1

    raise DatabaseConnectionError("Failed to connect to the database")

def init_db():
    conn = get_connection()
        
    try:
        with conn.cursor() as cur:
            cur.execute(SCHEMA)
        conn.commit()
        print("Database initialized successfully")
        return True

    except pymysql.Error as e:
        print(f"Database initialization error: {e}")
        raise DatabaseError(f"Failed to initialize the database: {e}")
    
    finally:
        conn.close()

def register_account(payload: AuthenticationPayload):
    conn = get_connection()
    
    try:
        with conn.cursor() as cur:
            hashed_password = crypt_context.hash(payload.password)

            cur.execute("SELECT mail FROM users WHERE mail=%s;", (payload.mail,))
            if cur.rowcount != 0:
                raise DatabaseAlreadyExistsError(f"An account with mail {payload.mail} already exists")
            
            cur.execute(
                "INSERT IGNORE INTO users (mail, password) VALUES (%s, %s);",
                (payload.mail, hashed_password)
            )

        conn.commit()
        print(f"Account registered successfully for {payload.mail}")
        return 0
    
    except pymysql.Error as e:
        print(f"Database error during account registration: {e}")
        raise DatabaseError(f"Account registration failed: {e}")
    
    finally:
        conn.close()


def authenticate_account(payload: AuthenticationPayload):
    conn = get_connection()
    
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id, password, has_premium FROM users WHERE mail=%s;", (payload.mail,))
            result = cur.fetchone()
            if not result:
                raise DatabaseNotFoundError(f"No account found with mail {payload.mail}.")
            
            if crypt_context.verify(payload.password, result["password"]):
                print(f"Authentication successful for {payload.mail}")
                return {"user_id": result["user_id"], "has_premium": result["has_premium"]}
            else:
                print(f"Authentication failed for {payload.mail}")
                return None
    
    except pymysql.Error as e:
        print(f"Database error during authentication: {e}")
        raise DatabaseError(f"Authentication query failed: {e}")
    
    finally:
        conn.close()

def delete_account(user_id: int):
    conn = get_connection()
    
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE user_id=%s;", (user_id,))
            if cur.rowcount == 0:
                raise DatabaseNotFoundError(f"User not found for user_id {user_id}")
            
            cur.execute("DELETE FROM users WHERE user_id=%s;", (user_id,))

        conn.commit()
        print(f"Account deleted successfully for user_id {user_id}")
    
    except pymysql.Error as e:
        print(f"Database error during account deletion: {e}")
        raise DatabaseError(f"Account deletion failed: {e}")
    
    finally:
        conn.close()

def get_user_profile(user_id: int):
    conn = get_connection()
    
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM user_profiles WHERE user_id=%s;", (user_id,))
            result = cur.fetchone()
            if not result:
                raise DatabaseNotFoundError(f"No profile found for user_id {user_id}")
            
            print(f"Profile retrieved successfully for user_id {user_id}")
            return result
    
    except pymysql.Error as e:
        print(f"Database error during profile retrieval: {e}")
        raise DatabaseError(f"Failed to retrieve user profile: {e}")
    
    finally:
        conn.close()

def update_user_profile(user_id: int, p: ProfileUpdatePayload):
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM user_profiles WHERE user_id=%s;", (user_id,))
            if cur.rowcount == 0:
                cur.execute("""
                    INSERT INTO user_profiles
                    (user_id, name, sex, birth_date, height, weight, target_weight, activity_level, goal_type)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                    """,
                    (user_id, p.name, p.sex, p.birth_date, p.height, p.weight, p.target_weight, p.activity_level, p.goal_type)
                )
            else:
                cur.execute(
                    """
                    UPDATE user_profiles
                    SET name=%s, sex=%s, birth_date=%s, height=%s, weight=%s, target_weight=%s, activity_level=%s, goal_type=%s
                    WHERE user_id=%s;
                    """,
                    (p.name, p.sex, p.birth_date, p.height, p.weight, p.target_weight, p.activity_level, p.goal_type, user_id)
                )

        conn.commit()
        print(f"Profile updated successfully for user_id {user_id}")

    except pymysql.Error as e:
        print(f"Database error during profile update: {e}")
        raise DatabaseError(f"Profile update failed: {e}")

    finally:
        conn.close()

def get_user_restrictions(user_id: int):
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM user_restrictions WHERE user_id=%s;", (user_id,))
            results = cur.fetchall()
            print(f"Restrictions retrieved successfully for user_id {user_id}")
            return results

    except pymysql.Error as e:
        print(f"Database error during restrictions retrieval: {e}")
        raise DatabaseError(f"Failed to retrieve user restrictions: {e}")

    finally:
        conn.close()

def add_user_restriction(user_id: int, payload: UserRestrictionPayload):
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO user_restrictions
                (user_id, restriction_type, restriction_value)
                VALUES (%s, %s, %s);
                """,
                (user_id, payload.restriction_type, payload.restriction_value)
            )
        conn.commit()
        print(f"Restriction added successfully for user_id {user_id}")

    except pymysql.Error as e:
        print(f"Database error during restriction addition: {e}")
        raise DatabaseError(f"Failed to add user restriction: {e}")
    
    finally:
        conn.close()

def delete_user_restriction(restriction_id: int, user_id: int):
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM user_restrictions WHERE restriction_id=%s AND user_id=%s;", (restriction_id, user_id))
            if cur.rowcount == 0:
                raise DatabaseNotFoundError(f"No restriction found with id {restriction_id} for user_id {user_id}")
            
            cur.execute("DELETE FROM user_restrictions WHERE restriction_id=%s AND user_id=%s;", (restriction_id, user_id))
        conn.commit()
        print(f"Restriction with id {restriction_id} deleted successfully for user_id {user_id}")

    except pymysql.Error as e:
        print(f"Database error during restriction deletion: {e}")
        raise DatabaseError(f"Failed to delete user restriction: {e}")

    finally:
        conn.close()

def get_food_logs(user_id: int, log_date: date):
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            if log_date:
                cur.execute("SELECT * FROM foodlogs WHERE user_id=%s AND date=%s;", (user_id, log_date))
            else:
                cur.execute("SELECT * FROM foodlogs WHERE user_id=%s;", (user_id,))
            results = cur.fetchall()
            print(f"Food log retrieved successfully for user_id {user_id} on {log_date}")
            return results

    except pymysql.Error as e:
        print(f"Database error during food log retrieval: {e}")
        raise DatabaseError(f"Failed to retrieve food log: {e}")

    finally:
        conn.close()

def add_food_log(user_id: int, p: FoodLogPayload):
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO foodlogs
                (user_id, food_name, calories, protein, carbs, fat, micros, serving_size, meal_type, date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """,
                (user_id, p.name, p.calories, p.proteins, p.carbohydrates, p.fats, 
                 json.dumps(p.micronutrients), p.serving_size, p.meal_type, p.log_date)
            )
        conn.commit()
        print(f"Food log added successfully for user_id {user_id}")

    except pymysql.Error as e:
        print(f"Database error during food log addition: {e}")
        raise DatabaseError(f"Failed to add food log: {e}")
    
    finally:
        conn.close()

def delete_food_log(foodlog_id: int, user_id: int):
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM foodlogs WHERE foodlog_id=%s AND user_id=%s;", (foodlog_id, user_id))
            if cur.rowcount == 0:
                raise DatabaseNotFoundError(f"No food log found with id {foodlog_id} for user_id {user_id}")
            
            cur.execute("DELETE FROM foodlogs WHERE foodlog_id=%s AND user_id=%s;", (foodlog_id, user_id))
        conn.commit()
        print(f"Food log with id {foodlog_id} deleted successfully for user_id {user_id}")

    except pymysql.Error as e:
        print(f"Database error during food log deletion: {e}")
        raise DatabaseError(f"Failed to delete food log: {e}")

    finally:
        conn.close()

def get_water_logs(user_id: int, log_date: date):
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            if log_date:
                cur.execute("SELECT * FROM waterlogs WHERE user_id=%s AND date=%s;", (user_id, log_date))
            else:
                cur.execute("SELECT * FROM waterlogs WHERE user_id=%s;", (user_id,))
            results = cur.fetchall()
            print(f"Water log retrieved successfully for user_id {user_id} on {log_date}")
            return results

    except pymysql.Error as e:
        print(f"Database error during water log retrieval: {e}")
        raise DatabaseError(f"Failed to retrieve water log: {e}")

    finally:
        conn.close()

def add_water_log(user_id: int, payload: WaterLogPayload):
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO waterlogs
                (user_id, amount, date)
                VALUES (%s, %s, %s);
                """,
                (user_id, payload.amount, payload.log_date)
            )
        conn.commit()
        print(f"Water log added successfully for user_id {user_id}")

    except pymysql.Error as e:
        print(f"Database error during water log addition: {e}")
        raise DatabaseError(f"Failed to add water log: {e}")
    
    finally:
        conn.close()

def delete_water_log(waterlog_id: int, user_id: int):
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM waterlogs WHERE waterlog_id=%s AND user_id=%s;", (waterlog_id, user_id))
            if cur.rowcount == 0:
                raise DatabaseNotFoundError(f"No water log found with id {waterlog_id} for user_id {user_id}")
            
            cur.execute("DELETE FROM waterlogs WHERE waterlog_id=%s AND user_id=%s;", (waterlog_id, user_id))
        conn.commit()
        print(f"Water log with id {waterlog_id} deleted successfully for user_id {user_id}")

    except pymysql.Error as e:
        print(f"Database error during water log deletion: {e}")
        raise DatabaseError(f"Failed to delete water log: {e}")

    finally:
        conn.close()

def get_weight_logs(user_id: int, log_date: date):
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            if log_date:
                cur.execute("SELECT * FROM weightlogs WHERE user_id=%s AND date=%s;", (user_id, log_date))
            else:
                cur.execute("SELECT * FROM weightlogs WHERE user_id=%s;", (user_id,))
            results = cur.fetchall()
            print(f"Weight log retrieved successfully for user_id {user_id} on {log_date}")
            return results

    except pymysql.Error as e:
        print(f"Database error during weight log retrieval: {e}")
        raise DatabaseError(f"Failed to retrieve weight log: {e}")

    finally:
        conn.close()

def add_weight_log(user_id: int, payload: WeightLogPayload):
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO weightlogs
                (user_id, weight, date)
                VALUES (%s, %s, %s);
                """,
                (user_id, payload.weight, payload.log_date)
            )
        conn.commit()
        print(f"Weight log added successfully for user_id {user_id}")

    except pymysql.Error as e:
        print(f"Database error during weight log addition: {e}")
        raise DatabaseError(f"Failed to add weight log: {e}")
    
    finally:
        conn.close()

def delete_weight_log(weightlog_id: int, user_id: int):
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM weightlogs WHERE weightlog_id=%s AND user_id=%s;", (weightlog_id, user_id))
            if cur.rowcount == 0:
                raise DatabaseNotFoundError(f"No weight log found with id {weightlog_id} for user_id {user_id}")
            
            cur.execute("DELETE FROM weightlogs WHERE weightlog_id=%s AND user_id=%s;", (weightlog_id, user_id))
        conn.commit()
        print(f"Weight log with id {weightlog_id} deleted successfully for user_id {user_id}")

    except pymysql.Error as e:
        print(f"Database error during weight log deletion: {e}")
        raise DatabaseError(f"Failed to delete weight log: {e}")

    finally:
        conn.close()