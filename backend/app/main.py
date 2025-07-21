"""Main FastAPI application module."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.routes import router as api_router

app = FastAPI(
    title="Smart Assistant for Video/Audio Content",
    description="A service that helps users extract insights from video and audio content",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)


@app.get("/")
async def root():
    """Root endpoint that returns a welcome message."""
    return {
        "message": "Welcome to the Smart Assistant API",
        "status": "operational",
        "version": "0.1.0",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


def run_api(host="0.0.0.0", port=8000):
    """Run FastAPI server using uvicorn.
    
    Args:
        host: Host to bind the server to.
        port: Port to bind the server to.
    """
    import uvicorn
    import os
    
    # Allow port override via environment variable
    port = int(os.environ.get("API_PORT", port))
    
    uvicorn.run("backend.app.main:app", host=host, port=port, reload=True)


if __name__ == "__main__":
    run_api()
