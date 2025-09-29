#!/bin/bash

# Start the FastAPI application
echo "Starting Shopping Analytics API..."
echo "Database Type: $DATABASE_TYPE"

if [ "$DATABASE_TYPE" = "postgres" ]; then
    echo "Using PostgreSQL: $POSTGRES_URL"
elif [ "$DATABASE_TYPE" = "mongodb" ]; then
    echo "Using MongoDB: $MONGODB_URL"
else
    echo "Error: DATABASE_TYPE must be 'postgres' or 'mongodb'"
    exit 1
fi

python -m app.main