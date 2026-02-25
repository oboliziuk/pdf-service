import io
import json
import logging
import time
from datetime import datetime

import boto3
from botocore.exceptions import ClientError
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_sqs_client():
    return boto3.client(
        "sqs",
        endpoint_url=settings.AWS_ENDPOINT_URL,
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.AWS_ENDPOINT_URL,
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )


def generate_pdf_bytes(email: str, name: str, surname: str, date_of_birth: str) -> bytes:
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    p.setFillColorRGB(0.18, 0.35, 0.6)
    p.rect(0, height - 80, width, 80, fill=True, stroke=False)
    p.setFillColorRGB(1, 1, 1)
    p.setFont("Helvetica-Bold", 22)
    p.drawString(40, height - 50, "User Profile")
    p.setFont("Helvetica", 10)
    p.drawString(40, height - 68, f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")

    p.setFillColorRGB(0, 0, 0)
    fields = [
        ("Name", name),
        ("Surname", surname),
        ("Email", email),
        ("Date of Birth", date_of_birth),
    ]
    y = height - 140
    for label, value in fields:
        p.setFont("Helvetica-Bold", 11)
        p.drawString(60, y, f"{label}:")
        p.setFont("Helvetica", 11)
        p.drawString(200, y, str(value))
        y -= 30

    p.save()
    buffer.seek(0)
    return buffer.read()


def ensure_queue_exists(sqs) -> str:
    try:
        response = sqs.create_queue(QueueName="pdf-jobs")
        return response["QueueUrl"]
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "QueueAlreadyExists":
            response = sqs.get_queue_url(QueueName="pdf-jobs")
            return response["QueueUrl"]
        raise


def ensure_bucket_exists(s3):
    try:
        s3.create_bucket(Bucket=settings.S3_BUCKET_NAME)
        logger.info(f"Created S3 bucket: {settings.S3_BUCKET_NAME}")
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code not in ("BucketAlreadyExists", "BucketAlreadyOwnedByYou"):
            raise


def process_message(message: dict):
    email = message["email"]
    name = message.get("name", "N/A")
    surname = message.get("surname", "N/A")
    date_of_birth = message.get("date_of_birth", "N/A")
    job_id = message.get("job_id", "unknown")

    logger.info(f"Processing job {job_id} for {email}")

    pdf_bytes = generate_pdf_bytes(email, name, surname, date_of_birth)

    s3 = get_s3_client()
    ensure_bucket_exists(s3)

    s3_key = f"profiles/{email}/{job_id}.pdf"
    s3.put_object(
        Bucket=settings.S3_BUCKET_NAME,
        Key=s3_key,
        Body=pdf_bytes,
        ContentType="application/pdf",
    )

    logger.info(f"Saved PDF to s3://{settings.S3_BUCKET_NAME}/{s3_key}")


def poll_queue():
    sqs = get_sqs_client()
    queue_url = ensure_queue_exists(sqs)
    logger.info(f"Polling SQS queue: {queue_url}")

    while True:
        try:
            response = sqs.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=10,
            )

            messages = response.get("Messages", [])
            if not messages:
                continue

            for msg in messages:
                try:
                    body = json.loads(msg["Body"])
                    process_message(body)

                    sqs.delete_message(
                        QueueUrl=queue_url,
                        ReceiptHandle=msg["ReceiptHandle"],
                    )
                    logger.info(f"Message processed and deleted")

                except Exception as e:
                    logger.error(f"Failed to process message: {e}")

        except ClientError as e:
            logger.error(f"SQS error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    time.sleep(5)
    poll_queue()
