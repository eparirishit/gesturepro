import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

def get_database_url():
    """Construct database URL based on environment"""
    # Check if we're running in Cloud Run (has Cloud SQL connection)
    if os.getenv('CLOUD_SQL_CONNECTION_NAME'):
        connection_name = os.getenv('CLOUD_SQL_CONNECTION_NAME')
        db_user = os.getenv('DB_USER', 'appuser')
        db_password = os.getenv('DB_PASSWORD')
        db_name = os.getenv('DB_NAME', 'gesturepro')
        
        return f"postgresql://{db_user}:{db_password}@/{db_name}?host=/cloudsql/{connection_name}"
    
    # Local development or explicit DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return database_url
    
    db_host = os.getenv('DB_HOST', '127.0.0.1')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'gesturepro')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', '')
    
    if not db_port or db_port == 'None':
        db_port = '5432'
    
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

DATABASE_URL = get_database_url()
print(f"Connecting to database: {DATABASE_URL.split('@')[0]}@***")  # Hide credentials in logs

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()