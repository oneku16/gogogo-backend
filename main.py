from fastapi import FastAPI
from app.representations.api.v1 import users, telegram, rides

app = FastAPI(
    title="Gogogo Backend",
    description="Backend API for Gogogo project",
    version="1.0.0",
)

app.include_router(users.router, prefix="/api/v1")
app.include_router(telegram.router, prefix="/api/v1")
app.include_router(rides.router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "ok"}
