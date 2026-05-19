import pymysql
from .core import get_connection, crypt_context, DatabaseError, DatabaseNotFoundError, DatabaseAlreadyExistsError
from schemas import AuthenticationPayload, ProfileUpdatePayload, UserRestrictionPayload

# ====== Account Management ======

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
            cur.execute("DELETE FROM users WHERE user_id=%s;", (user_id,))
            if cur.rowcount == 0:
                raise DatabaseNotFoundError(f"User not found for user_id {user_id}")

        conn.commit()
        print(f"Account deleted successfully for user_id {user_id}")
    
    except pymysql.Error as e:
        print(f"Database error during account deletion: {e}")
        raise DatabaseError(f"Account deletion failed: {e}")
    
    finally:
        conn.close()


# ====== Profile Management ======

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


# ====== Restrictions Management ======

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
            cur.execute("DELETE FROM user_restrictions WHERE restriction_id=%s AND user_id=%s;", (restriction_id, user_id))
            if cur.rowcount == 0:
                raise DatabaseNotFoundError(f"No restriction found with id {restriction_id} for user_id {user_id}")
        conn.commit()
        print(f"Restriction with id {restriction_id} deleted successfully for user_id {user_id}")

    except pymysql.Error as e:
        print(f"Database error during restriction deletion: {e}")
        raise DatabaseError(f"Failed to delete user restriction: {e}")

    finally:
        conn.close()
