from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.auth import router as auth_router
from app.api.routes.events import router as events_router
from app.api.routes.registrations import router as registrations_router
from app.api.routes.admins import router as admins_router


app = FastAPI(
    title="Registration System API",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://gcl-registrations-frontend-a584q6isf-sheyiewonders-projects.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(admins_router)
app.include_router(events_router)
app.include_router(registrations_router)


@app.get("/")
def root():
    return {
        "message": "Registration API is running"
    }