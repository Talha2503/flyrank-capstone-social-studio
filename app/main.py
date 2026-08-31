from fastapi import FastAPI
from app.routers import posts

app = FastAPI(title="Social Media Studio")

app.include_router(posts.router)


@app.get("/")
def root():
    return {"status": "ok"}