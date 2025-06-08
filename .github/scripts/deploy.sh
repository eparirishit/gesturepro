#!/bin/bash

# This script handles the deployment process for the application.

# Exit immediately if a command exits with a non-zero status
set -e

# Function to deploy database
deploy_database() {
    echo "Deploying Cloud SQL database..."
    
    # Check if database instance exists
    if ! gcloud sql instances describe $DATABASE_INSTANCE_NAME --project=$GCP_PROJECT_ID 2>/dev/null; then
        echo "Creating new Cloud SQL instance..."
        gcloud sql instances create $DATABASE_INSTANCE_NAME \
            --database-version=POSTGRES_14 \
            --tier=db-f1-micro \
            --region=$GCP_REGION \
            --project=$GCP_PROJECT_ID
        
        # Create database
        gcloud sql databases create gesturepro \
            --instance=$DATABASE_INSTANCE_NAME \
            --project=$GCP_PROJECT_ID
    else
        echo "Database instance already exists, skipping creation..."
    fi
}

# Function to deploy backend
deploy_backend() {
    echo "Building Docker image for the backend..."
    docker build -t gcr.io/$GCP_PROJECT_ID/backend:latest -f .github/docker/Dockerfile.prod .

    echo "Pushing Docker image to Google Container Registry..."
    docker push gcr.io/$GCP_PROJECT_ID/backend:latest

    echo "Deploying the backend to Google Cloud Run..."
    gcloud run deploy $BACKEND_SERVICE_NAME \
        --image gcr.io/$GCP_PROJECT_ID/backend:latest \
        --platform managed \
        --region $GCP_REGION \
        --allow-unauthenticated \
        --project $GCP_PROJECT_ID \
        --add-cloudsql-instances=$GCP_PROJECT_ID:$GCP_REGION:$DATABASE_INSTANCE_NAME
}

# Main deployment logic
case "$1" in
    "database")
        deploy_database
        ;;
    "backend")
        deploy_backend
        ;;
    "all"|*)
        deploy_database
        deploy_backend
        ;;
esac

echo "Deployment completed successfully."/backend:latest -f .github/docker/Dockerfile.prod .