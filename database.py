from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os
from dotenv import load_dotenv


load_dotenv()

engine = create_async_engine(os.getenv("DATABASE_URL"))

new_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_session():
    async with new_session() as session:
        yield session


async def setup_database():
    async with engine.begin() as connecion:
        await connecion.run_sync(Base.metadata.create_all)









