from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.database import get_db
import app.crud as crud
from app.api.routes.auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.db.models import DBUser
from app.schemas import UserBase, UserCreate, UserLogin
from fastapi.responses import StreamingResponse
from reportlab.pdfgen import canvas
import io


app = FastAPI(title="FastAPI Authentication with Database", version="1.0.0")


@app.post("/register", response_model=UserBase)
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = await crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = await crud.create_user(db=db, user=user)
    return UserBase(
        name=new_user.name,
        surname=new_user.surname,
        email=new_user.email,
        date_of_birth=new_user.date_of_birth,
    )


@app.post("/login")
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    db_user = await crud.authenticate_user(db, user.email, user.password)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.email},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/token")
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db)
):
    user = await crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/profile/pdf")
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
