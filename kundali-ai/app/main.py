from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.routes import location  
import uvicorn

app = FastAPI(title="Kundali AI")

# 1. Enable CORS to allow requests from file:// or other domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Include API Routes (Adjust import path if necessary)
try:
    from app.api.v1.router import api_router
    api_router.include_router(location.router, tags=["locations"]) 
    app.include_router(api_router, prefix="/api/v1")
except ImportError:
    print("WARNING: Could not import api_router from app.api.v1.router. Please verify your API router location.")

# 3. Mount the UI
app.mount("/ui", StaticFiles(directory="app/ui/templates", html=True), name="ui")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)