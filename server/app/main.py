import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import auth
from .api.sign_detector import router as sign_detector_router
from .services.model_service import model_service
from .services.model_downloader import model_downloader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

try:
    from .models.user import Base
    from .utils.db import engine
    
    if engine:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    else:
        logger.warning("Database engine not available")
except Exception as e:
    logger.error(f"Database initialization failed: {e}")

app = FastAPI(
    title="GesturePro API",
    description="Sign Language Detection and Translation API using YOLOv8",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    app.include_router(auth.router, prefix="/auth", tags=["authentication"])
    logger.info("Auth router included")
except Exception as e:
    logger.error(f"Failed to include auth router: {e}")

try:
    app.include_router(sign_detector_router, prefix="/api/sign", tags=["sign_detection"])
    logger.info("Sign detector router included")
except Exception as e:
    logger.error(f"Failed to include sign detector router: {e}")

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("🚀 Starting GesturePro API...")
    logger.info(f"PORT environment variable: {os.getenv('PORT', 'Not set')}")
    
    # Check if we're in cloud environment
    is_cloud = os.getenv('CLOUD_SQL_CONNECTION_NAME') is not None
    logger.info(f"Environment: {'Cloud' if is_cloud else 'Local'}")
    
    # Model loading with cloud support
    try:
        if is_cloud:
            # Check GCS connection first
            logger.info("Checking Google Cloud Storage connection...")
            if model_downloader.check_gcs_connection():
                logger.info("✅ GCS connection successful")
            else:
                logger.warning("⚠️ GCS connection failed, API will start without ML capabilities")
                return
        
        logger.info("📦 Loading model...")
        success = model_service.load_model()
        
        if success:
            logger.info("✅ Model loaded successfully!")
        else:
            logger.warning("⚠️ Failed to load model, API will start without ML capabilities")
            
    except Exception as e:
        logger.error(f"Model service initialization failed: {e}")

@app.get("/")
async def root():
    return {
        "message": "GesturePro API - Sign Language Detection",
        "status": "running",
        "version": "1.0.0",
        "model_loaded": model_service.is_loaded,
        "model_type": "YOLOv8 PyTorch",
        "environment": "cloud" if os.getenv('CLOUD_SQL_CONNECTION_NAME') else "local",
        "port": os.getenv('PORT', '8000')
    }

@app.get("/health")
async def health_check():
    model_info = model_service.get_model_info() if model_service.is_loaded else {}
    
    return {
        "status": "healthy",
        "model_loaded": model_service.is_loaded,
        "database": "connected",
        "model_info": model_info,
        "environment": "cloud" if os.getenv('CLOUD_SQL_CONNECTION_NAME') else "local",
        "port": os.getenv('PORT', '8000')
    }