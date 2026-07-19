from sqlalchemy import ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base
from datetime import date


class UserModel(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    nick: Mapped[str] = mapped_column(unique=True)
    email:  Mapped[str] = mapped_column(unique=True)
    password: Mapped[str] = mapped_column()
    listings: Mapped[list["ListingModel"]] = relationship(back_populates="owner")
    bookings: Mapped[list["BookingModel"]] = relationship(back_populates="guest")

class ListingModel(Base):
    __tablename__ = "listings"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    description: Mapped[str] = mapped_column() 
    price: Mapped[float] = mapped_column()
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    owner: Mapped["UserModel"] = relationship(back_populates="listings")
    bookings: Mapped[list["BookingModel"]] = relationship(back_populates="listing")


class BookingModel(Base):
    __tablename__ = "bookings"
    id: Mapped[int] = mapped_column(primary_key=True)
    check_in: Mapped[date] = mapped_column()
    check_out: Mapped[date] = mapped_column()
    guest_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"))
    status: Mapped[str] = mapped_column()
    guest: Mapped["UserModel"] = relationship(back_populates="bookings")
    listing: Mapped["ListingModel"] = relationship(back_populates="bookings")