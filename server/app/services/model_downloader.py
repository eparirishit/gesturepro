import os
import logging
from typing import Optional, Tuple
from google.cloud import storage
import tempfile

logger = logging.getLogger(__name__)

class ModelDownloader:
    """Downloads models from Google Cloud Storage"""
    
    def __init__(self):
        self.client = None
        self.bucket_name = os.getenv('GCS_BUCKET_NAME', 'gesturepro-models')
        self.model_cache_dir = '/tmp/models'
        
        # Create cache directory
        os.makedirs(self.model_cache_dir, exist_ok=True)
        
    def _get_client(self) -> storage.Client:
        """Get or create GCS client"""
        if self.client is None:
            try:
                # In Cloud Run, this will use the service account automatically
                self.client = storage.Client()
                logger.info("Google Cloud Storage client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize GCS client: {e}")
                raise
        return self.client
    
    def download_file_from_gcs(self, gcs_path: str, local_path: str) -> bool:
        """Download a file from Google Cloud Storage"""
        try:
            client = self._get_client()
            bucket = client.bucket(self.bucket_name)
            blob = bucket.blob(gcs_path)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Download the file
            logger.info(f"Downloading {gcs_path} from GCS bucket {self.bucket_name}")
            blob.download_to_filename(local_path)
            
            if os.path.exists(local_path):
                file_size = os.path.getsize(local_path)
                logger.info(f"Successfully downloaded {gcs_path} ({file_size} bytes)")
                return True
            else:
                logger.error(f"File not found after download: {local_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error downloading {gcs_path}: {e}")
            return False
    
    def get_model_paths(self) -> Tuple[Optional[str], Optional[str]]:
        """Get local paths for model files, downloading from GCS if needed"""
        
        # Check if we're in a cloud environment
        is_cloud = os.getenv('CLOUD_SQL_CONNECTION_NAME') is not None
        
        if is_cloud:
            logger.info("Cloud environment detected, downloading models from GCS")
            return self._download_models_from_gcs()
        else:
            logger.info("Local environment detected, using local model paths")
            return self._get_local_model_paths()
    
    def _download_models_from_gcs(self) -> Tuple[Optional[str], Optional[str]]:
        """Download models from Google Cloud Storage"""
        
        # Define GCS paths and local cache paths
        model_gcs_path = os.getenv('GCS_MODEL_PATH', 'models/yolo/yolo_best.pt')
        class_names_gcs_path = os.getenv('GCS_CLASS_NAMES_PATH', 'models/yolo/class_names.json')
        
        model_local_path = os.path.join(self.model_cache_dir, 'yolo_best.pt')
        class_names_local_path = os.path.join(self.model_cache_dir, 'class_names.json')
        
        # Check if files already exist in cache
        model_exists = os.path.exists(model_local_path)
        class_names_exists = os.path.exists(class_names_local_path)
        
        # Download model file if not cached
        if not model_exists:
            logger.info("Model file not in cache, downloading from GCS...")
            if not self.download_file_from_gcs(model_gcs_path, model_local_path):
                logger.error("Failed to download model file")
                return None, None
        else:
            logger.info("Model file found in cache")
        
        # Download class names file if not cached
        if not class_names_exists:
            logger.info("Class names file not in cache, downloading from GCS...")
            if not self.download_file_from_gcs(class_names_gcs_path, class_names_local_path):
                logger.error("Failed to download class names file")
                return None, None
        else:
            logger.info("Class names file found in cache")
        
        return model_local_path, class_names_local_path
    
    def _get_local_model_paths(self) -> Tuple[Optional[str], Optional[str]]:
        """Get local model paths for development"""
        
        model_path = os.environ.get('YOLO_MODEL_PATH')
        class_names_path = os.environ.get('CLASS_NAMES_PATH')
        
        if not model_path:
            model_path = os.path.join("ml", "saved_models", "yolo", "yolo_best.pt")
        
        if not class_names_path:
            class_names_path = os.path.join("ml", "saved_models", "yolo", "class_names.json")
        
        # Check if files exist
        if os.path.exists(model_path) and os.path.exists(class_names_path):
            return model_path, class_names_path
        else:
            logger.warning(f"Local model files not found: {model_path}, {class_names_path}")
            return None, None
    
    def check_gcs_connection(self) -> bool:
        """Check if we can connect to GCS and the bucket exists"""
        try:
            client = self._get_client()
            bucket = client.bucket(self.bucket_name)
            bucket.exists()
            logger.info(f"Successfully connected to GCS bucket: {self.bucket_name}")
            return True
        except Exception as e:
            logger.error(f"Cannot connect to GCS bucket {self.bucket_name}: {e}")
            return False

# Global instance
model_downloader = ModelDownloader()