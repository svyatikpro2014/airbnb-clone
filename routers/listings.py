from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from database import get_session
from models import UserModel, ListingModel
from schemas import ListingAddSchema, ListingResponceSchema, ListingUpdateSchema
from routers.auth import get_user
from sqlalchemy.orm import selectinload


router = APIRouter(prefix="/listings", tags=["listings"])


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
    
    await session.delete(obj)
    await session.commit()