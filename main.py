from fastapi import FastAPI
import uvicorn
from database import setup_database
import models 

app = FastAPI()


@app.on_event("startup")
async def startup():
    await setup_database()


if __name__ == "__main__":
    uvicorn.run(app="main:app", reload=True)