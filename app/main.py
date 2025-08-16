from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.api import auth, users, transactions, reports


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    yield
    # Shutdown
    await close_mongo_connection()


app = FastAPI(
    title="Financial Management System",
    description="A FastAPI-based financial management system with role-based access control",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
app.include_router(reports.router, prefix="/reports", tags=["Reports"])


@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    return {"message": "Financial Management System API", "version": "1.0.0"}


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "healthy"}