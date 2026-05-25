import json
import pymysql
from datetime import date

from schemas import DietMealPayload, DietProgramPayload
from .core import get_connection, DatabaseError, DatabaseNotFoundError


# ====== Diet Program Management ======

def get_user_diet_programs(user_id: int):
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM diet_program WHERE user_id=%s;", (user_id,))
            results = cur.fetchall()
            print(f"Diet programs retrieved successfully for user_id {user_id}")
            return results

    except pymysql.Error as e:
        print(f"Database error during diet programs retrieval: {e}")
        raise DatabaseError(f"Failed to retrieve diet programs: {e}")

    finally:
        conn.close()


def create_diet_program(user_id: int, p: DietProgramPayload):
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO diet_program
                (user_id, start_date, end_date, target_calories, target_protein, target_carbs, target_fat, goal_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                """,
                (user_id, p.start_date, p.end_date, p.target_calories, p.target_protein, p.target_carbs, p.target_fat, p.goal_type)
            )
        conn.commit()
        diet_id = cur.lastrowid
        print(f"Diet program created successfully for user_id {user_id} with diet_id {diet_id}")
        return diet_id

    except pymysql.Error as e:
        print(f"Database error during diet program creation: {e}")
        raise DatabaseError(f"Failed to create diet program: {e}")

    finally:
        conn.close()


def delete_diet_program(diet_id: int, user_id: int):
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM diet_program WHERE diet_id=%s AND user_id=%s;", (diet_id, user_id))
            if cur.rowcount == 0:
                raise DatabaseNotFoundError(f"No diet program found with id {diet_id} for user_id {user_id}")
        conn.commit()
        print(f"Diet program with id {diet_id} deleted successfully for user_id {user_id}")

    except pymysql.Error as e:
        print(f"Database error during diet program deletion: {e}")
        raise DatabaseError(f"Failed to delete diet program: {e}")

    finally:
        conn.close()


# ====== Diet Meals Management ======

def get_diet_meals(diet_id: int, user_id: int):
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT dm.* FROM diet_meals dm
                JOIN diet_program dp ON dm.diet_id = dp.diet_id
                WHERE dm.diet_id = %s AND dp.user_id = %s;
                """,
                (diet_id, user_id)
            )
            results = cur.fetchall()
            print(f"Diet meals retrieved successfully for diet_id {diet_id}")
            return results

    except pymysql.Error as e:
        print(f"Database error during diet meals retrieval: {e}")
        raise DatabaseError(f"Failed to retrieve diet meals: {e}")

    finally:
        conn.close()


def add_diet_meal(diet_id: int, p: DietMealPayload, user_id: int):
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO diet_meals (diet_id, meal_name, calories, protein, carbs, fat)
                SELECT %s, %s, %s, %s, %s, %s
                WHERE EXISTS (
                    SELECT 1
                    FROM diet_program dp
                    WHERE dp.diet_id = %s AND dp.user_id = %s
                );
                """,
                (diet_id, p.meal_name, p.calories, p.proteins, p.carbs, p.fats, diet_id, user_id)
            )
            if cur.rowcount == 0:
                raise DatabaseNotFoundError(f"No diet program found with id {diet_id} for user_id {user_id}")

        conn.commit()
        print(f"Diet meal '{p.meal_name}' added successfully to diet_id {diet_id} for user_id {user_id}")

    except pymysql.Error as e:
        print(f"Database error during diet meal addition: {e}")
        raise DatabaseError(f"Failed to add diet meal: {e}")

    finally:
        conn.close()


def delete_diet_meal(meal_id: int, diet_id: int, user_id: int):
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE dm FROM diet_meals dm
                JOIN diet_program dp ON dm.diet_id = dp.diet_id
                WHERE dm.meal_id = %s 
                    AND dm.diet_id = %s 
                    AND dp.user_id = %s;
                """,
                (meal_id, diet_id, user_id)
            )

            if cur.rowcount == 0:
                raise DatabaseNotFoundError(f"No diet meal found with id {meal_id} for diet_id {diet_id} and user_id {user_id}")
            
        conn.commit()
        print(f"Diet meal with id {meal_id} deleted successfully from diet_id {diet_id} for user_id {user_id}")

    except pymysql.Error as e:
        print(f"Database error during diet meal deletion: {e}")
        raise DatabaseError(f"Failed to delete diet meal: {e}")

    finally:
        conn.close()
