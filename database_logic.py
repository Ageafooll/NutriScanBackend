import pymysql
from passlib.context import CryptContext

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


#
#   Adding user to database
#
def add_user(username: str, password: str):

    try:
        connection = pymysql.connect(
            host=HOST,
            user=USER,
            password=PASSWORD,
            database=DATABASE,
            port=PORT,
            cursorclass=pymysql.cursors.DictCursor
        )        
    except pymysql.Error as e:
        printf(f"Niye baglanamadi? {e}")
        return 2


    init_sql = '''CREATE TABLE IF NOT EXISTS users (
             user_id INT AUTO_INCREMENT PRIMARY KEY,
             username VARCHAR(30) UNIQUE,
             password VARCHAR(255),
             is_premium INT,
             active INT) AUTO_INCREMENT = 1000; '''
    
    check_sql = "SELECT username FROM users WHERE username=%s;"
             
    insert_sql = "INSERT INTO users (username, password, is_premium, active) VALUES (%s, %s, 0, 1);"
             

    hashed_password = crypt_context.hash(password)

    try:
        with connection.cursor() as cursor:

            cursor.execute(init_sql)

            cursor.execute(check_sql, (username))

            if(cursor.rowcount != 0):
                print(f"User {username} already exists")
                return 3       

            cursor.execute(insert_sql, (username, hashed_password))

            connection.commit()
            print(f"created the user {username}")

    except pymysql.Error as e:
        print(f"query'de hata {e}")
        return 4


    finally:
        connection.close()

    return 1



def authenticate_user(username: str, password: str ):

    try:
        connection = pymysql.connect(
            host="db_service",
            user="python_api",
            password="1234",
            database="users_db",
            port=3306,
            cursorclass=pymysql.cursors.DictCursor
        )        
    except pymysql.Error as e:
        printf(f"Niye baglanamadi? {e}")
        return 2

    auth_sql = "SELECT password FROM users WHERE username=%s;"
    info_sql = "SELECT user_id, is_premium FROM users WHERE username=%s;"


    try:
        with connection.cursor() as cursor:

            cursor.execute(auth_sql,(username,))

            if(cursor.rowcount == 0):
                print(f"User {username} doesn't exists")
                return 3           


            result = cursor.fetchone()

            if(crypt_context.verify(password, result["password"])):

                print(f"Password auth was successful for {username}")

                cursor.execute(info_sql,(username,))

                result = cursor.fetchone()

                user_id = result["user_id"]
                is_premium = result["is_premium"]
            
            else:
                return 3
            

    except pymysql.Error as e:
        print(f"query'de hata {e}")
        return 4

    finally:
        connection.close()

    
    return {"user_id": user_id, "is_premium": is_premium}