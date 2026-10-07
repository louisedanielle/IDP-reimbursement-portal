"""
Tiny FastAPI app used only to satisfy Render's web service port check.
Celery runs in the background via the start command.
"""
from fastapi import FastAPI

app = FastAPI(title="Reimbursement Worker Healthcheck")


@app.get("/")
async def root():
    return {"status": "worker-running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}