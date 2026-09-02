from fastapi import FastAPI

app = FastAPI(
    title="TARK",
    description="Reason Before Risk — Autonomous AI-Powered Options Trading Agent",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "name": "TARK",
        "message": "Reason Before Risk",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
    }