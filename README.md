This repository holds the backend of the **NutriScan** application with the following deployment diagram:

<img width="994" height="932" alt="Screenshot_20261029_143929" src="https://github.com/user-attachments/assets/a7b48553-f126-4a18-923d-53ab6d36fdec" />


The security of API endpoints are ensured by requiring authorization for them, **JWT**s are issued for authorizing the users to endpoints:

<img width="754" height="662" alt="Screenshot_20261029_144459" src="https://github.com/user-attachments/assets/e07e6bb4-8622-47ca-8a07-a590a6e2defd" />


Before a JWT is issued to a user they must be authenticated against the user database, password information are kept secure by **Argon2** hashing algorithm.
The databases are protected from SQL injection attacks by using **prepared statements** for queries:

<img width="940" height="712" alt="Screenshot_20261029_145538" src="https://github.com/user-attachments/assets/eb7c1429-d8e6-416b-a482-9aaaacc53d23" />


Current state of this project still has flaws hence it is not fit to be used in production

```
docker compose up --build -d
```
