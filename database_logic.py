import os
import pymysql
from passlib.context import CryptContext

# DB variables — loaded from environment with safe defaults for local dev
HOST     = os.getenv("DB_HOST",     "db_service")
USER     = os.getenv("DB_USER",     "python_api")
PASSWORD = os.getenv("DB_PASSWORD", "1234")
DATABASE = os.getenv("DB_NAME",     "users_db")
PORT     = int(os.getenv("DB_PORT", "3306"))

# Hashing algorithm we will use
crypt_context = CryptContext(
        schemes=["argon2"],
        default="argon2",
        deprecated="auto",
    )

#
#   Database connections and queries implemented here
#


def _get_connection():
    """Opens and returns a new pymysql connection."""
    return pymysql.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        database=DATABASE,
        port=PORT,
        cursorclass=pymysql.cursors.DictCursor
    )


# ---------------------------------------------------------------------------
#   Schema helpers
# ---------------------------------------------------------------------------

_INIT_USERS_SQL = """
CREATE TABLE IF NOT EXISTS users (
    user_id            INT AUTO_INCREMENT PRIMARY KEY,
    username           VARCHAR(30) UNIQUE,
    password           VARCHAR(255),
    is_premium         INT          DEFAULT 0,
    active             INT          DEFAULT 1,
    weight             FLOAT        DEFAULT NULL,
    goal_weight        FLOAT        DEFAULT NULL,
    daily_calorie_goal INT          DEFAULT NULL
) AUTO_INCREMENT = 1000;
"""

_INIT_MEALS_SQL = """
CREATE TABLE IF NOT EXISTS meals (
    meal_id        INT AUTO_INCREMENT PRIMARY KEY,
    user_id        INT          NOT NULL,
    name           VARCHAR(255) NOT NULL,
    gram           INT          NOT NULL,
    calories       INT          NOT NULL,
    proteins       INT          NOT NULL,
    carbohydrates  INT          NOT NULL,
    fats           INT          NOT NULL,
    created_at     TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
"""

def _ensure_schema(cursor):
    """Create tables if they don't exist yet."""
    cursor.execute(_INIT_USERS_SQL)
    cursor.execute(_INIT_MEALS_SQL)


# ---------------------------------------------------------------------------
#   User management
# ---------------------------------------------------------------------------

def add_user(username: str, password: str):

    try:
        connection = _get_connection()
    except pymysql.Error as e:
        print(f"Niye baglanamadi? {e}")
        return 2

    check_sql  = "SELECT username FROM users WHERE username=%s;"
    insert_sql = "INSERT INTO users (username, password, is_premium, active) VALUES (%s, %s, 0, 1);"

    hashed_password = crypt_context.hash(password)

    try:
        with connection.cursor() as cursor:
            _ensure_schema(cursor)

            cursor.execute(check_sql, (username,))

            if cursor.rowcount != 0:
                print(f"User {username} already exists")
                return 3

            cursor.execute(insert_sql, (username, hashed_password))
            connection.commit()
            print(f"Created the user {username}")

    except pymysql.Error as e:
        print(f"Query'de hata {e}")
        return 4

    finally:
        connection.close()

    return 1


def authenticate_user(username: str, password: str):

    try:
        connection = _get_connection()
    except pymysql.Error as e:
        print(f"Niye baglanamadi? {e}")
        return 2

    auth_sql = "SELECT password FROM users WHERE username=%s;"
    info_sql = "SELECT user_id, is_premium FROM users WHERE username=%s;"

    try:
        with connection.cursor() as cursor:

            cursor.execute(auth_sql, (username,))

            if cursor.rowcount == 0:
                print(f"User {username} doesn't exist")
                return 3

            result = cursor.fetchone()

            if crypt_context.verify(password, result["password"]):
                print(f"Password auth was successful for {username}")
                cursor.execute(info_sql, (username,))
                result    = cursor.fetchone()
                user_id   = result["user_id"]
                is_premium = result["is_premium"]
            else:
                return 3

    except pymysql.Error as e:
        print(f"Query'de hata {e}")
        return 4

    finally:
        connection.close()

    return {"user_id": user_id, "is_premium": is_premium}


def remove_user(username: str):

    try:
        connection = _get_connection()
    except pymysql.Error as e:
        print(f"Niye baglanamadi? {e}")
        return 2

    check_sql  = "SELECT username FROM users WHERE username=%s;"
    remove_sql = "DELETE FROM users WHERE username=%s;"

    try:
        with connection.cursor() as cursor:

            cursor.execute(check_sql, (username,))

            if cursor.rowcount == 0:
                print(f"User {username} doesn't exist")
                return 3

            cursor.execute(remove_sql, (username,))
            connection.commit()
            print(f"Removed the user {username}")

    except pymysql.Error as e:
        print(f"Query'de hata {e}")
        return 4

    finally:
        connection.close()

    return 1


# ---------------------------------------------------------------------------
#   Meal history
# ---------------------------------------------------------------------------

def save_meal(user_id: int, meal_data: dict):
    """
    Persists a meal scan result for a user.

    meal_data keys: name, gram, calories, proteins, carbohydrates, fats
    Returns 1 on success, 2 on connection error, 4 on query error.
    """
    try:
        connection = _get_connection()
    except pymysql.Error as e:
        print(f"save_meal – connection error: {e}")
        return 2

    insert_sql = """
        INSERT INTO meals (user_id, name, gram, calories, proteins, carbohydrates, fats)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
    """

    try:
        with connection.cursor() as cursor:
            _ensure_schema(cursor)
            cursor.execute(insert_sql, (
                user_id,
                meal_data.get("name"),
                meal_data.get("gram"),
                meal_data.get("calories"),
                meal_data.get("proteins"),
                meal_data.get("carbohydrates"),
                meal_data.get("fats"),
            ))
            connection.commit()
            print(f"Saved meal '{meal_data.get('name')}' for user {user_id}")

    except pymysql.Error as e:
        print(f"save_meal – query error: {e}")
        return 4

    finally:
        connection.close()

    return 1


def get_meal_history(user_id: int):
    """
    Returns a list of all meals for the given user, newest first.
    Returns an empty list on DB errors (non-critical path).
    """
    try:
        connection = _get_connection()
    except pymysql.Error as e:
        print(f"get_meal_history – connection error: {e}")
        return []

    select_sql = """
        SELECT meal_id, name, gram, calories, proteins, carbohydrates, fats, created_at
        FROM meals
        WHERE user_id = %s
        ORDER BY created_at DESC;
    """

    try:
        with connection.cursor() as cursor:
            _ensure_schema(cursor)
            cursor.execute(select_sql, (user_id,))
            rows = cursor.fetchall()
            # Convert datetime objects to ISO strings for JSON serialisation
            for row in rows:
                if row.get("created_at"):
                    row["created_at"] = row["created_at"].isoformat()
            return rows

    except pymysql.Error as e:
        print(f"get_meal_history – query error: {e}")
        return []

    finally:
        connection.close()


# ---------------------------------------------------------------------------
#   User profile
# ---------------------------------------------------------------------------

def get_user_profile(user_id: int):
    """
    Returns weight, goal_weight, and daily_calorie_goal for the user.
    Returns None on error.
    """
    try:
        connection = _get_connection()
    except pymysql.Error as e:
        print(f"get_user_profile – connection error: {e}")
        return None

    select_sql = "SELECT weight, goal_weight, daily_calorie_goal FROM users WHERE user_id = %s;"

    try:
        with connection.cursor() as cursor:
            cursor.execute(select_sql, (user_id,))
            return cursor.fetchone()

    except pymysql.Error as e:
        print(f"get_user_profile – query error: {e}")
        return None

    finally:
        connection.close()


def update_user_profile(user_id: int, profile_data: dict):
    """
    Updates weight, goal_weight, and/or daily_calorie_goal for the user.
    Only fields present in profile_data are updated.
    Returns 1 on success, 2 on connection error, 4 on query error.
    """
    allowed_fields = {"weight", "goal_weight", "daily_calorie_goal"}
    updates = {k: v for k, v in profile_data.items() if k in allowed_fields and v is not None}

    if not updates:
        return 1  # Nothing to update

    try:
        connection = _get_connection()
    except pymysql.Error as e:
        print(f"update_user_profile – connection error: {e}")
        return 2

    set_clause = ", ".join(f"{col} = %s" for col in updates)
    update_sql = f"UPDATE users SET {set_clause} WHERE user_id = %s;"

    try:
        with connection.cursor() as cursor:
            cursor.execute(update_sql, (*updates.values(), user_id))
            connection.commit()
            print(f"Updated profile for user {user_id}: {updates}")

    except pymysql.Error as e:
        print(f"update_user_profile – query error: {e}")
        return 4

    finally:
        connection.close()

    return 1
