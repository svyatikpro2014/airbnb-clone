from fastapi import FastAPI
import uvicorn
from database import setup_database
import models 
from routers.listings import router as listings_router
from routers.auth import router as auth_router
from routers.bookings import router as bookings_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


app.include_router(listings_router)
app.include_router(auth_router)
app.include_router(bookings_router)

@app.on_event("startup")
async def startup():
    await setup_database()


if __name__ == "__main__":
    uvicorn.run(app="main:app", reload=True)