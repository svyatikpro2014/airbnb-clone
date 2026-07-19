from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase


engine = create_async_engine("sqlite+aiosqlite:///airbnb.db")

new_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_session():
    async with new_session() as session:
        yield session


async def setup_database():
    async with engine.begin() as connecion:
        await connecion.run_sync(Base.metadata.create_all)









