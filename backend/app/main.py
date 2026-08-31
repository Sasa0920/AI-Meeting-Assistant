from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import meetings

app = FastAPI(title="AI Meeting Assistant API")

# Setup CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Since it's local development, allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(meetings.router)

@app.get("/health")
def health():
    return {"status": "ok"}