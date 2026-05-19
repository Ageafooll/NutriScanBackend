import json
import pymysql
from datetime import date
from .core import get_connection, DatabaseError, DatabaseNotFoundError
from schemas import FoodLogPayload, WaterLogPayload, WeightLogPayload


# ====== Food Logging ======

def get_food_logs(user_id: int, log_date: date = None):
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
            cur.execute("DELETE FROM foodlogs WHERE foodlog_id=%s AND user_id=%s;", (foodlog_id, user_id))
            if cur.rowcount == 0:
                raise DatabaseNotFoundError(f"No food log found with id {foodlog_id} for user_id {user_id}")
        conn.commit()
        print(f"Food log with id {foodlog_id} deleted successfully for user_id {user_id}")

    except pymysql.Error as e:
        print(f"Database error during food log deletion: {e}")
        raise DatabaseError(f"Failed to delete food log: {e}")

    finally:
        conn.close()


# ====== Water Logging ======

def get_water_logs(user_id: int, log_date: date = None):
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
            cur.execute("DELETE FROM waterlogs WHERE waterlog_id=%s AND user_id=%s;", (waterlog_id, user_id))
            if cur.rowcount == 0:
                raise DatabaseNotFoundError(f"No water log found with id {waterlog_id} for user_id {user_id}")
        conn.commit()
        print(f"Water log with id {waterlog_id} deleted successfully for user_id {user_id}")

    except pymysql.Error as e:
        print(f"Database error during water log deletion: {e}")
        raise DatabaseError(f"Failed to delete water log: {e}")

    finally:
        conn.close()


# ====== Weight Logging ======

def get_weight_logs(user_id: int, log_date: date = None):
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
            cur.execute("DELETE FROM weightlogs WHERE weightlog_id=%s AND user_id=%s;", (weightlog_id, user_id))
            if cur.rowcount == 0:
                raise DatabaseNotFoundError(f"No weight log found with id {weightlog_id} for user_id {user_id}")
        conn.commit()
        print(f"Weight log with id {weightlog_id} deleted successfully for user_id {user_id}")

    except pymysql.Error as e:
        print(f"Database error during weight log deletion: {e}")
        raise DatabaseError(f"Failed to delete weight log: {e}")

    finally:
        conn.close()
