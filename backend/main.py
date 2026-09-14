from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import sys

# Add backend directory to path so imports work if run from project root
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from inference import PlaylifyModel

app = FastAPI(
    title="Playlify ML API",
    description="API for classifying album covers into musical genres",
    version="1.0.0"
)

# Enable CORS for the frontend
frontend_url = os.environ.get("FRONTEND_URL", "")

# We want to support local development and the deployed frontend.
allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://localhost:3000",
]

if frontend_url and frontend_url != "*":
    for url in frontend_url.split(","):
        url = url.strip().rstrip("/")
        if url and url not in allowed_origins:
            allowed_origins.append(url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if frontend_url == "*" else allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model instance
model_instance = None

@app.on_event("startup")
async def startup_event():
    global model_instance
    # Resolve absolute path to models directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    models_dir = os.path.join(base_dir, "models")
    
    if not os.path.exists(models_dir):
        print(f"ERROR: Models directory not found at {models_dir}")
        print("Please ensure you have run the training pipeline.")
        return
        
    try:
        model_instance = PlaylifyModel(models_dir=models_dir)
    except Exception as e:
        print(f"Failed to load models: {e}")

@app.get("/health")
async def health_check():
    if model_instance is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {"status": "ok"}

@app.post("/predict")
async def predict_genre(image: UploadFile = File(...), k: int = Form(10)):
    print(f"Received predict request. File: {image.filename}, Type: {image.content_type}, K: {k}")
    if model_instance is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
        
    if image.content_type and not image.content_type.startswith("image/"):
        print(f"Rejected: Invalid content type {image.content_type}")
        raise HTTPException(status_code=400, detail="File must be an image")
        
    try:
        # Read the image bytes
        image_bytes = await image.read()
        print(f"Read {len(image_bytes)} bytes")
        
        # Run inference
        results = model_instance.predict(image_bytes, num_neighbors=k)
        print("Inference successful")
        return JSONResponse(content=results)
        
    except ValueError as e:
        print(f"ValueError during prediction: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during prediction")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False if os.environ.get("RENDER") else True)
