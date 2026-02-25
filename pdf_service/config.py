from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    AWS_ENDPOINT_URL: str = "http://localstack:4566"
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = "test"
    AWS_SECRET_ACCESS_KEY: str = "test"
    SQS_QUEUE_URL: str = "http://localstack:4566/000000000000/pdf-jobs"
    S3_BUCKET_NAME: str = "pdf-profiles"

    model_config = ConfigDict(
        env_file=".env",
        extra="ignore"
    )

settings = Settings()
