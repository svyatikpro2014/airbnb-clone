from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_session
from models import UserModel, RefreshTokenModel
from schemas import UserAddSchema, UserResponseSchema, UserLoginSchema, RefreshTokenSchema
from passlib.context import CryptContext
from authx import AuthX, AuthXConfig, TokenPayload 
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from sqlalchemy.orm import joinedload


router = APIRouter(prefix="/auth", tags=["auth"])

load_dotenv()

config = AuthXConfig()

config.JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
config.JWT_TOKEN_LOCATION = ["headers"]
config.JWT_HEADER_NAME = "Authorization"
config.JWT_HEADER_TYPE = "Bearer"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") 

security = AuthX(config=config)


def hash_password(password:str)->str:
    return pwd_context.hash(password)


def verify_password(password:str, hashed_password:str)->bool:
    return pwd_context.verify(password, hashed_password)


def hash_token(token: str) -> str:
    return sha256(token.encode()).hexdigest()


@router.post("/registration", response_model=UserResponseSchema)
async def register(user:UserAddSchema, session:AsyncSession = Depends(get_session)):
    exist_check = await session.execute(select(UserModel).where(UserModel.email == user.email))
    exists = exist_check.scalar_one_or_none()

    if exists:
        raise HTTPException(detail="email already used", status_code=400)
    
    hashed = hash_password(user.password.get_secret_value())

    new_user = UserModel(email= user.email, password= hashed, nick= user.nick)
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user


@router.post("/login")
async def login(user:UserLoginSchema, session:AsyncSession = Depends(get_session)):
    exist_check = await session.execute(select(UserModel).where(UserModel.email == user.email))
    existing_user = exist_check.scalar_one_or_none()

    if not existing_user:
        raise HTTPException(detail="Invalid credentials", status_code=401)
    
    if not verify_password(user.password.get_secret_value(), existing_user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = security.create_access_token(uid=str(existing_user.id))
    refresh_token = security.create_refresh_token(uid=str(existing_user.id))
    db_refresh_token = hash_token(refresh_token)

    r_token = RefreshTokenModel(hashed_token= db_refresh_token, expiry= datetime.now(timezone.utc) + timedelta(days=20), user = existing_user)
    session.add(r_token)
    await session.commit()
    return {"access_token": access_token, "refresh_token": refresh_token, "type": "bearer"}


@router.post("/refresh")
async def refresh(raw_token: RefreshTokenSchema, session: AsyncSession = Depends(get_session)):
    hashed = hash_token(raw_token.refresh_token)
    query = await session.execute(select(RefreshTokenModel).where (RefreshTokenModel.hashed_token == hashed))
    r_token = query.scalar_one_or_none()

    if r_token and not r_token.revoked and r_token.expiry > datetime.now(timezone.utc):
        access_token = security.create_access_token(uid=str(r_token.user_id))
    else:
        raise HTTPException(status_code= 401, detail="Session expired")

    return {"access_token": access_token}


@router.post("/logout")
async def logout(raw_token: RefreshTokenSchema, session: AsyncSession = Depends(get_session)):
    hashed = hash_token(raw_token.refresh_token)
    query = await session.execute(select(RefreshTokenModel).where(RefreshTokenModel.hashed_token == hashed))
    r_token = query.scalar_one_or_none()

    if not r_token:
        raise HTTPException(status_code=401, detail="Invalid token")

    r_token.revoked = True
    await session.commit()

    return {"msg": "Logged out"}


async def get_user(payload: TokenPayload = Depends(security.access_token_required), session: AsyncSession = Depends(get_session)):
    id = payload.sub

    result = await session.execute(select(UserModel).where(UserModel.id == int(id)))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


@router.get("/me", response_model=UserResponseSchema)
async def get_me(current_user = Depends(get_user)):
    return current_user