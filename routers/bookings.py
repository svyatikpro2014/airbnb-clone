from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from database import get_session
from models import UserModel, BookingModel, ListingModel
from schemas import BookingAddSchema, BookingResponceSchema
from routers.auth import get_user
from sqlalchemy.orm import selectinload


router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.get("/as-owner", response_model=list[BookingResponceSchema])
async def get_bookings_owner(session: AsyncSession = Depends(get_session), current_user = Depends(get_user)):
    result = await session.execute(select(BookingModel)
        .join(ListingModel)
        .where(ListingModel.user_id == current_user.id)
        .options(selectinload(BookingModel.guest),selectinload(BookingModel.listing)))
    
    return result.scalars().all()


@router.get("/as-guest", response_model=list[BookingResponceSchema])
async def get_bookings_owner(session: AsyncSession = Depends(get_session), current_user = Depends(get_user)):
    result = await session.execute(select(BookingModel)
        .where(BookingModel.guest_id == current_user.id)
        .options(selectinload(BookingModel.guest),selectinload(BookingModel.listing)))
    
    return result.scalars().all()


@router.post("/", response_model=BookingResponceSchema)
async def add_booking(booking: BookingAddSchema, current_user = Depends(get_user), session: AsyncSession = Depends(get_session)):
    listing = await session.get(ListingModel, booking.listing_id)
    if not listing:
        raise HTTPException(detail="Listing not found", status_code=404)

    if current_user.id == listing.user_id:
        raise HTTPException(detail="Not allowed", status_code=403)

    obj = BookingModel(check_in=booking.check_in, check_out=booking.check_out, guest_id= current_user.id, status= "pending", guest= current_user, listing= listing)
    
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj