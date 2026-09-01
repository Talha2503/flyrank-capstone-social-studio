from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from app.routers import posts, reviews
from app.scheduler import start_scheduler

app = FastAPI(title="Social Media Studio")

app.include_router(posts.router)
app.include_router(reviews.router)

_scheduler = None


@app.on_event("startup")
def on_startup():
    global _scheduler
    _scheduler = start_scheduler()


@app.get("/")
def root():
    return {"status": "ok"}