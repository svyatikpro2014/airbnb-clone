from pydantic import BaseModel, EmailStr, SecretStr, Field, ConfigDict
from typing import Literal
from datetime import date


class UserAddSchema(BaseModel):
    nick: str
    email: EmailStr
    password: SecretStr = Field(min_length=5, max_length=72)


class UserResponseSchema(BaseModel):
    id: int
    email: str
    nick: str


class ListingAddSchema(BaseModel):
    name: str = Field(min_length=4, max_length=30)
    description: str = Field(min_length=1, max_length=200) 
    price: float = Field(gt=0)


class UserShortSchema(BaseModel):
    id: int
    nick: str

    model_config = ConfigDict(from_attributes=True)


class ListingResponceSchema(BaseModel):
    id: int
    name: str = Field(min_length=4, max_length=30)
    description: str = Field(min_length=1, max_length=200) 
    price: float = Field(gt=0)
    owner: UserShortSchema
    model_config = ConfigDict(from_attributes=True)


class ListingUpdateSchema(BaseModel):
    name: str = Field(min_length=4, max_length=30)
    description: str = Field(min_length=1, max_length=200) 
    price: float = Field(gt=0)


class BookingAddSchema(BaseModel):
    listing_id: int
    check_in: date
    check_out: date


class ListingShortSchema(BaseModel):
    id: int
    name: str
    description: str
    price: float
    model_config = ConfigDict(from_attributes=True)
    

class BookingResponceSchema(BaseModel):
    id: int
    check_in: date
    check_out: date
    status: Literal["pending", "confirmed", "rejected", "cancelled"]
    guest: UserShortSchema
    listing: ListingShortSchema
    model_config = ConfigDict(from_attributes=True)