from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from database import get_session
from models import UserModel, ListingModel, BookingModel
from schemas import ListingAddSchema, ListingResponceSchema, ListingUpdateSchema
from routers.auth import get_user
from sqlalchemy.orm import selectinload
import os
import uuid


router = APIRouter(prefix="/listings", tags=["listings"])

UPLOAD_DIR = "static/uploads"

@router.get("/", response_model=list[ListingResponceSchema])
async def get_listings(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(ListingModel).options(selectinload(ListingModel.owner)))
    return result.scalars().all()


@router.post("/", response_model=ListingResponceSchema)
async def add_listing(listing: ListingAddSchema, current_user = Depends(get_user), session: AsyncSession = Depends(get_session)):
    obj = ListingModel(**listing.model_dump(),  owner=current_user)
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


@router.patch("/{listing_id}", response_model=ListingResponceSchema)
async def update_listing(listing_update: ListingUpdateSchema, listing_id:int, current_user = Depends(get_user), session: AsyncSession = Depends(get_session)):
    tem = await session.execute(select(ListingModel).where(ListingModel.id == listing_id).options(selectinload(ListingModel.owner)))
    obj = tem.scalar_one_or_none()

    if not obj:
        raise HTTPException(detail="Listing not found", status_code=404)
    
    if obj.owner.id != current_user.id:
        raise HTTPException(detail="Permission denied", status_code=403)
    
    for key, value in listing_update.model_dump().items():
        setattr(obj, key, value)

    await session.commit()
    await session.refresh(obj)
    return obj  


@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_listing(listing_id:int, current_user = Depends(get_user), session: AsyncSession = Depends(get_session)):
    tem = await session.execute(select(ListingModel).where(ListingModel.id == listing_id).options(selectinload(ListingModel.owner)))
    obj = tem.scalar_one_or_none()

    if not obj:
        raise HTTPException(detail="Listing not found", status_code=404)
    
    if obj.owner.id != current_user.id:
        raise HTTPException(detail="Permission denied", status_code=403)
    
    active_bookings = await session.execute(select(BookingModel).where(BookingModel.listing_id == listing_id, BookingModel.status.in_(["pending", "confirmed"])))
    
    if active_bookings.scalars().first():
        raise HTTPException(status_code=400, detail="Cannot delete listing with active bookings")

    await session.delete(obj)
    await session.commit()


@router.post("/{listing_id}/photo", response_model=ListingResponceSchema)
async def upload_photo(
    listing_id: int,
    photo: UploadFile = File(...),
    current_user = Depends(get_user),
    session: AsyncSession = Depends(get_session)
):
    tem = await session.execute(select(ListingModel).where(ListingModel.id == listing_id).options(selectinload(ListingModel.owner)))
    obj = tem.scalar_one_or_none()

    if not obj:
        raise HTTPException(detail="Listing not found", status_code=404)

    if obj.owner.id != current_user.id:
        raise HTTPException(detail="Permission denied", status_code=403)

    ext = os.path.splitext(photo.filename)[1] #creating file .extension
    filename = f"{uuid.uuid4().hex}{ext}" #creating random filename + .ext
    filepath = os.path.join(UPLOAD_DIR, filename) #generating path of the file

    contents = await photo.read() #read the foto
    with open(filepath, "wb") as f: 
        f.write(contents)  #write into new file

    obj.image_url = f"/static/uploads/{filename}" #url for db

    await session.commit()
    await session.refresh(obj)
    return obj