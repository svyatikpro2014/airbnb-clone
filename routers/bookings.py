from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from database import get_session
from models import UserModel, BookingModel, ListingModel
from schemas import BookingAddSchema, BookingResponceSchema
from routers.auth import get_user
from sqlalchemy.orm import selectinload
from datetime import date


router = APIRouter(prefix="/bookings", tags=["bookings"])


async def date_crossing(sess: AsyncSession, listing_id: int, check_in: date, check_out: date) -> bool:   
    result = await sess.execute(select(BookingModel).where(BookingModel.listing_id == listing_id, check_in < BookingModel.check_out, check_out > BookingModel.check_in, BookingModel.status == "confirmed"))
    booking = result.scalars().first()
    return booking is not None

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
    result = await session.execute(select(ListingModel).where(ListingModel.id == booking.listing_id).options(selectinload(ListingModel.owner)))
    
    listing = result.scalar_one_or_none()

    if not listing:
        raise HTTPException(detail="Listing not found", status_code=404)

    if current_user.id == listing.user_id:
        raise HTTPException(detail="Not allowed", status_code=403)
    
    overlap = await date_crossing(session, booking.listing_id, booking.check_in, booking.check_out)
    if overlap:
         raise HTTPException(detail="Date is already booked", status_code=400)

    obj = BookingModel(check_in=booking.check_in, check_out=booking.check_out, guest_id= current_user.id, status= "pending", guest= current_user, listing= listing)
    
    session.add(obj)
    await session.commit()

    return obj



@router.patch("/{booking_id}/confirm", response_model=BookingResponceSchema)
async def confirm_booking(booking_id: int, current_user = Depends(get_user), session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(BookingModel).where(BookingModel.id == booking_id).options(selectinload(BookingModel.listing), selectinload(BookingModel.guest)))
    booking = res.scalar_one_or_none()

    if not booking:
        raise HTTPException(detail="booking not found", status_code=404)
    
    if current_user.id != booking.listing.user_id:
        raise HTTPException(detail="permission denied", status_code=403)
    
    booking.status = "confirmed"

    await session.commit()
    await session.refresh(booking)
    return booking
    

@router.patch("/{booking_id}/reject", response_model=BookingResponceSchema)
async def reject_booking(booking_id: int, current_user = Depends(get_user), session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(BookingModel).where(BookingModel.id == booking_id).options(selectinload(BookingModel.listing), selectinload(BookingModel.guest)))
    booking = res.scalar_one_or_none()

    if not booking:
        raise HTTPException(detail="booking not found", status_code=404)
    
    if current_user.id != booking.listing.user_id:
        raise HTTPException(detail="permission denied", status_code=403)
    
    booking.status = "rejected"

    await session.commit()
    await session.refresh(booking)
    return booking
    

@router.patch("/{booking_id}/cancel", response_model=BookingResponceSchema)
async def cancel_booking(booking_id: int, current_user = Depends(get_user), session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(BookingModel).where(BookingModel.id == booking_id).options(selectinload(BookingModel.listing), selectinload(BookingModel.guest)))
    booking = res.scalar_one_or_none()

    if not booking:
        raise HTTPException(detail="booking not found", status_code=404)
    
    if current_user.id != booking.guest_id:
        raise HTTPException(detail="permission denied", status_code=403)
    
    booking.status = "cancelled"

    await session.commit()
    await session.refresh(booking)
    return booking