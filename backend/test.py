#!/usr/bin/env python3
"""
Test script to verify all dependencies are installed
"""
try:
    import fastapi
    print("✅ FastAPI installed")
except ImportError as e:
    print("❌ FastAPI missing:", e)

try:
    from pydantic_settings import BaseSettings
    print("✅ pydantic-settings installed")
except ImportError as e:
    print("❌ pydantic-settings missing:", e)

try:
    import google.generativeai
    print("✅ google-generativeai installed")
except ImportError as e:
    print("❌ google-generativeai missing:", e)

try:
    import sqlalchemy
    print("✅ SQLAlchemy installed")
except ImportError as e:
    print("❌ SQLAlchemy missing:", e)

try:
    import pymongo
    print("✅ PyMongo installed")
except ImportError as e:
    print("❌ PyMongo missing:", e)

print("\nAll dependencies checked!")
