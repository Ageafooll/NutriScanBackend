This repository holds the backend of the **NutriScan** application with the following deployment diagram:
<br>
<img width="994" height="932" alt="Screenshot_20261029_143929" src="https://github.com/user-attachments/assets/a7b48553-f126-4a18-923d-53ab6d36fdec" />
<br>
<br>
The security of API endpoints are ensured by requiring authorization for them, **JWT**s are issued for authorizing the users to endpoints:
<br>
<img width="754" height="662" alt="Screenshot_20261029_144459" src="https://github.com/user-attachments/assets/e07e6bb4-8622-47ca-8a07-a590a6e2defd" />
<br>
<br>
Before a JWT is issued to a user they must be authenticated against the user database, password information are kept secure by **Argon2** hashing algorithm.
The databases are protected from SQL injection attacks by using **prepared statements** for queries:
<br>
<img width="827" height="881" alt="Screenshot_20261029_152212" src="https://github.com/user-attachments/assets/a27106bb-9867-4b8b-9a67-70d2226079dc" />
<br>
<br>
Prompts to self hosted LLMs are (mostly) protected from prompt injection attacks by isolating AI engine to their own container (like all other services) with absolutely no access to other services other than the API Gateway:
<br>
<img width="699" height="622" alt="Screenshot_20261029_152945" src="https://github.com/user-attachments/assets/d0d7477f-bfdb-420d-9402-013a0f3ee1a6" />
<br>
<br>
Current state of this project still has flaws hence it is not fit to be used in production
<br>
```
docker compose up --build -d
```
