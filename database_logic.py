import pymysql
from passlib.context import CryptContext
from time import sleep

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
        has_premium INT
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

    CREATE TABLE IF NOT EXISTS diet_program (
        diet_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        start_date DATE,
        end_date DATE,
        total_calories INT,
        total_protein INT,
        total_carbs INT,
        total_fat INT
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

class DatabaseError(Exception):
    pass

class DatabaseConnectionError(Exception):
    pass

class AccountAlreadyExistsError(DatabaseError):
    def __init__(self, mail):
        super().__init__(f"An account with mail {mail} already exists.")

class AccountNotFoundError(DatabaseError):
    def __init__(self, mail):
        super().__init__(f"No account found with mail {mail}.")

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

def register_account(mail: str, password: str):
    conn = get_connection()
    
    try:
        with conn.cursor() as cur:
            hashed_password = crypt_context.hash(password)

            cur.execute("SELECT mail FROM users WHERE mail=%s;", (mail,))
            if cur.rowcount != 0:
                raise AccountAlreadyExistsError(mail)
            
            cur.execute(
                "INSERT IGNORE INTO users (mail, password, has_premium) VALUES (%s, %s, 0);",
                (mail, hashed_password)
            )

        conn.commit()
        print(f"Account registered successfully for {mail}")
        return 0
    
    except pymysql.Error as e:
        print(f"Database error during account registration: {e}")
        raise DatabaseError(f"Account registration failed: {e}")
    
    finally:
        conn.close()


def authenticate_account(mail: str, password: str):
    conn = get_connection()
    
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id, password, has_premium FROM users WHERE mail=%s;", (mail,))
            result = cur.fetchone()
            if not result:
                raise AccountNotFoundError(mail)
            
            if crypt_context.verify(password, result["password"]):
                print(f"Authentication successful for {mail}")
                return {"user_id": result["user_id"], "has_premium": result["has_premium"]}
            else:
                print(f"Authentication failed for {mail}")
                return None
    
    except pymysql.Error as e:
        print(f"Database error during authentication: {e}")
        raise DatabaseError(f"Authentication query failed: {e}")
    
    finally:
        conn.close()

def delete_account(mail: str):
    conn = get_connection()
    
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE mail=%s;", (mail,))
            if cur.rowcount == 0:
                raise AccountNotFoundError(mail)
            
            cur.execute("DELETE FROM users WHERE mail=%s;", (mail,))

        conn.commit()
        print(f"Account deleted successfully for {mail}")
    
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
                raise DatabaseError(f"No profile found for user_id {user_id}")
            
            print(f"Profile retrieved successfully for user_id {user_id}")
            return result
    
    except pymysql.Error as e:
        print(f"Database error during profile retrieval: {e}")
        raise DatabaseError(f"Failed to retrieve user profile: {e}")
    
    finally:
        conn.close()

def update_user_profile(user_id: int, name: str, sex: str, birth_date: str, height: int, weight: int, target_weight: int, activity_level: str, goal_type: str):
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
                    (user_id, name, sex, birth_date, height, weight, target_weight, activity_level, goal_type)
                )
            else:
                cur.execute(
                    """
                    UPDATE user_profiles
                    SET name=%s, sex=%s, birth_date=%s, height=%s, weight=%s, target_weight=%s, activity_level=%s, goal_type=%s
                    WHERE user_id=%s;
                    """,
                    (name, sex, birth_date, height, weight, target_weight, activity_level, goal_type, user_id)
                )

        conn.commit()
        print(f"Profile updated successfully for user_id {user_id}")

    except pymysql.Error as e:
        print(f"Database error during profile update: {e}")
        raise DatabaseError(f"Profile update failed: {e}")

    finally:
        conn.close()


