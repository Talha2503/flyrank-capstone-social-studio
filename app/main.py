from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from app.routers import posts, reviews

app = FastAPI(title="Social Media Studio")

app.include_router(posts.router)
app.include_router(reviews.router)


@app.get("/")
def root():
    return {"status": "ok"}