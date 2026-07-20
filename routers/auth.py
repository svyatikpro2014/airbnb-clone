from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_session
from models import UserModel
from schemas import UserAddSchema, UserResponseSchema
from passlib.context import CryptContext
from authx import AuthX, AuthXConfig, TokenPayload 
import os
from dotenv import load_dotenv


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
async def login(user:UserAddSchema, session:AsyncSession = Depends(get_session)):
    exist_check = await session.execute(select(UserModel).where(UserModel.email == user.email))
    existing_user = exist_check.scalar_one_or_none()

    if not existing_user:
        raise HTTPException(detail="user does not exist", status_code=400)
    
    if not verify_password(user.password.get_secret_value(), existing_user.password):
        raise HTTPException(status_code=401, detail="Wrong password")
    
    token = security.create_access_token(uid=str(existing_user.id))
    return {"access token": token, "type": "bearer"}



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