import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from api.routes import users, teachers, rooms, subjects, classes, auth, timetables, payments, assignments, public_v1, public, schools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/app.log', mode='a') if os.path.exists('logs') else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="EduSchedule API",
    description="Backend services for the EduSchedule AI-assisted timetabling system.",
    version="0.1.0",
)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Use env var for origins, default to localhost for dev
origins_str = os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
origins = origins_str.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all the routers
app.include_router(auth.router)
app.include_router(teachers.router)
app.include_router(rooms.router)
app.include_router(subjects.router)
app.include_router(classes.router)
app.include_router(timetables.router)
app.include_router(users.router)
app.include_router(public_v1.router)
app.include_router(assignments.router)
app.include_router(public.router)
app.include_router(payments.router)
app.include_router(schools.router)

@app.get("/")
def read_root():
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to the EduSchedule API!"}

@app.on_event("startup")
async def startup_event():
    logger.info("EduSchedule API starting up...")
    logger.info(f"CORS Origins: {origins}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("EduSchedule API shutting down...")
