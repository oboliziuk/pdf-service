# PDF Backend Project

An asynchronous REST API built with FastAPI, PostgreSQL, SQLAlchemy (async), Alembic, and Docker.

## Tech Stack

- FastAPI
- PostgreSQL
- SQLAlchemy (Async)
- Alembic (Database migrations)
- Pydantic v2
- Docker & Docker Compose
- bcrypt
- ReportLab
- AWS SQS
- AWS S3
- LocalStack
- Docker & Docker Compose


## Project Structure

```
NewApiProjects/
│
├── auth_service/
│   ├── app/
│   │   ├── main.py
│   │   ├── schemas.py
│   │   ├── crud.py
│   │   ├── api/
│   │   │   ├── deps.py
│   │   │   └── routes/
│   │   │       └── auth.py
│   │   ├── core/
│   │   │   └── config.py
│   │   └── db/
│   │       ├── database.py
│   │       └── models.py
│   ├── alembic/
│   ├── alembic.ini
│   ├── Dockerfile
│   ├── requirements.txt
│   └── requirements-test.txt
│
├── pdf_service/
│   ├── pdf.py
│   ├── worker.py
│   ├── config.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── localstack-init/
│   └── init.sh
│
├── tests/
│   ├── conftest.py
│   └── test_auth.py
│
├── docker-compose.yml
├── .env.example
└── README.md
```


## Environment Variables

Create a `.env` file based on `.env.example`.

Example:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/postgres
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AWS LocalStack
AWS_ENDPOINT_URL=http://localstack:4566
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
SQS_QUEUE_URL=http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/pdf-jobs
S3_BUCKET_NAME=pdf-profiles
```

Do not commit your `.env` file to GitHub.

---

## Run with Docker

### Build and start containers

```bash
docker compose up --build
```

### Stop containers

```bash
docker compose down
```

### Stop and remove volumes
```bash
docker compose down -v
```

---

## Database Migrations (Alembic)

### Apply migrations

```bash
docker compose exec backend alembic upgrade head
```

### Create a new migration

```bash
docker compose exec backend alembic revision --autogenerate -m "migration message"
```

---

## API Documentation

Once the server is running:

- Swagger UI (auth): http://localhost:8000/docs
- Swagger UI (pdf): http://localhost:8001/docs


---

## Main Features

- User registration and authentication
- JWT-based authorization
- PDF export of user profile

---

## Verify S3 Upload

```
docker exec localstack awslocal s3 ls s3://pdf-profiles/profiles/ --recursive
```

##  Author

Oksana Boliziuk
