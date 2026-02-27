import json
import uuid
import io
from datetime import datetime

import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, HTTPException, FastAPI
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

from config import settings


router = APIRouter()
security = HTTPBearer()


def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {
            "email": email,
            "name": payload.get("name", "N/A"),
            "surname": payload.get("surname", "N/A"),
            "date_of_birth": payload.get("date_of_birth", "N/A"),
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")


def get_sqs_client():
    return boto3.client(
        "sqs",
        endpoint_url=settings.AWS_ENDPOINT_URL,
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )


@router.get("/profile/pdf")
async def download_profile_pdf(current_user: dict = Depends(get_current_user_from_token)):
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
        ("Name", current_user["name"]),
        ("Surname", current_user["surname"]),
        ("Email", current_user["email"]),
        ("Date of Birth", current_user["date_of_birth"]),
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

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=profile_{current_user['email']}.pdf"},
    )


@router.post("/profile/pdf/save")
async def save_profile_pdf_to_s3(current_user: dict = Depends(get_current_user_from_token)):
    message = {
        "job_id": str(uuid.uuid4()),
        "email": current_user["email"],
        "name": current_user["name"],
        "surname": current_user["surname"],
        "date_of_birth": str(current_user["date_of_birth"]),
    }

    try:
        sqs = get_sqs_client()
        queue_url = sqs.create_queue(QueueName="pdf-jobs")["QueueUrl"]
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message),
        )
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue job: {str(e)}")

    return {
        "message": "PDF save job queued successfully",
        "job_id": message["job_id"],
        "email": current_user["email"],
    }


app = FastAPI(title="PDF Service", version="1.0.0")
app.include_router(router)
