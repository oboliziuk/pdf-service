import json
import uuid
import io

from botocore.exceptions import ClientError

import boto3
from fastapi import APIRouter, Depends, HTTPException
from reportlab.pdfgen import canvas

from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer

from app.api.deps import get_current_user
from app.db.models import DBUser
from pdf_service.config import settings

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://auth-service:8000/login")

@router.get("/profile/pdf")
async def download_profile_pdf(
        current_user: DBUser = Depends(get_current_user),
):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)

    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 800, "User Profile")

    p.setFont("Helvetica", 12)
    p.drawString(100, 760, f"Name:         {current_user.name}")
    p.drawString(100, 740, f"Surname:      {current_user.surname}")
    p.drawString(100, 720, f"Email:        {current_user.email}")
    p.drawString(100, 700, f"Date of Birth: {current_user.date_of_birth}")

    p.save()
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=profile_{current_user.email}.pdf"}
    )

def get_sqs_client():
    return boto3.client(
        "sqs",
        endpoint_url=settings.AWS_ENDPOINT_URL,
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )


@router.post("/profile/pdf/save")
async def save_profile_pdf_to_s3(
    current_user: DBUser = Depends(get_current_user),
):

    message = {
        "job_id": str(uuid.uuid4()),
        "email": current_user.email,
        "name": current_user.name,
        "surname": current_user.surname,
        "date_of_birth": str(current_user.date_of_birth),
    }

    try:
        sqs = get_sqs_client()
        sqs.send_message(
            QueueUrl=settings.SQS_QUEUE_URL,
            MessageBody=json.dumps(message),
        )
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue job: {str(e)}")

    return {
        "message": "PDF save job queued successfully",
        "job_id": message["job_id"],
        "email": current_user.email,
    }
