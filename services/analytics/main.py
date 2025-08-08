from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("📊 Analytics Service started")
    yield
    print("📊 Analytics Service stopped")

app = FastAPI(title="Analytics Microservice", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
async def root():
    return {"service": "Analytics", "version": "3.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    print("📊 Starting Analytics on port 8002...")
    uvicorn.run(app, host="0.0.0.0", port=8002, reload=True)