import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

def get_database_url():
    """Construct database URL based on environment"""
    try:
        # Check if we're running in Cloud Run (has Cloud SQL connection)
        if os.getenv('CLOUD_SQL_CONNECTION_NAME'):
            connection_name = os.getenv('CLOUD_SQL_CONNECTION_NAME')
            db_user = os.getenv('DB_USER', 'appuser')
            db_password = os.getenv('DB_PASSWORD')
            db_name = os.getenv('DB_NAME', 'gesturepro')
            
            if not db_password:
                raise ValueError("DB_PASSWORD is required for Cloud SQL connection")
            
            return f"postgresql://{db_user}:{db_password}@/{db_name}?host=/cloudsql/{connection_name}"
        
        database_url = os.getenv('DATABASE_URL')
        if database_url and database_url != 'None':
            return database_url
        
        db_host = os.getenv('DB_HOST', '127.0.0.1')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME', 'gesturepro')
        db_user = os.getenv('DB_USER', 'postgres')
        db_password = os.getenv('DB_PASSWORD', '')
        
        if not db_port or db_port in ['None', 'null', '']:
            db_port = '5432'
        
        try:
            int(db_port)
        except (ValueError, TypeError):
            print(f"Warning: Invalid port '{db_port}', using default 5432")
            db_port = '5432'
        
        return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
    except Exception as e:
        print(f"Error constructing database URL: {e}")
        # Return a fallback URL for local development
        return "postgresql://postgres:@127.0.0.1:5432/gesturepro"

DATABASE_URL = get_database_url()
print(f"Database connection configured")

# Create engine with better error handling
try:
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=False  # Set to True for debugging SQL queries
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    print("Database engine created successfully")
except Exception as e:
    print(f"Error creating database engine: {e}")
    # Create a dummy engine for development
    engine = None
    SessionLocal = None

Base = declarative_base()

def get_db():
    if SessionLocal is None:
        raise RuntimeError("Database not properly configured")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()