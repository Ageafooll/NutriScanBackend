FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir fastapi uvicorn pydantic requests pymysql passlib passlib[argon2] pyjwt

COPY *.py /app/

CMD ["uvicorn", "api_gateway:app", "--host", "0.0.0.0", "--port", "3131", "--reload"]
