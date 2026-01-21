# eduschedule-backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import users, teachers, rooms, subjects, classes, auth, timetables, payments, assignments, public_v1, public, schools

app = FastAPI(
    title="EduSchedule API",
    description="Backend services for the EduSchedule AI-assisted timetabling system.",
    version="0.1.0",
)

# Define the list of origins that are allowed to make requests
origins = [
    "http://localhost:5173",
]

# Add the CORS middleware to the application
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
app.include_router(public.router) # Add the new public router
app.include_router(payments.router)
app.include_router(schools.router)

@app.get("/")
def read_root():
    """A simple endpoint to confirm the API is running."""
    return {"message": "Welcome to the EduSchedule API!"}