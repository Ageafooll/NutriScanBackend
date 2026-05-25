import pymysql
from passlib.context import CryptContext
from time import sleep

# Database configuration
HOST = "db_service"
USER = "python_api"
PASSWORD = "1234"
DATABASE = "nutriscan_db"
PORT = 3306

# Hashing algorithm
crypt_context = CryptContext(
    schemes=["argon2"],
    default="argon2",
    deprecated="auto",
)

# Database schema
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
        goal_type VARCHAR(20), -- LOSE_WEIGHT, MAINTAIN_WEIGHT, GAIN_WEIGHT, GAIN_MUSCLE

        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
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


# ====== Error Handling ======

class DatabaseError(Exception):
    """Base exception for database errors"""
    pass


class DatabaseConnectionError(DatabaseError):
    """Exception for database connection failures"""
    pass


class DatabaseAlreadyExistsError(DatabaseError):
    """Exception when resource already exists"""
    pass


class DatabaseNotFoundError(DatabaseError):
    """Exception when resource is not found"""
    pass


# ====== Connection Management ======

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

    except pymysql.Error as e:
        print(f"Database initialization error: {e}")
        raise DatabaseError(f"Failed to initialize the database: {e}")
    
    finally:
        conn.close()
