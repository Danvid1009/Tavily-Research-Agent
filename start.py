#!/usr/bin/env python3
"""
AgentResearch Startup Script
Checks prerequisites and provides setup instructions.
"""

import os
import sys
import subprocess
import requests
import json
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 9):
        print("❌ Python 3.9 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python {sys.version.split()[0]} - Compatible")
    return True

def check_dependencies():
    """Check if required packages are installed."""
    required_packages = [
        'fastapi', 'uvicorn', 'pydantic', 'langchain', 'langgraph',
        'tavily-python', 'pymongo', 'motor', 'httpx', 'python-dotenv'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} - Installed")
        except ImportError:
            print(f"❌ {package} - Missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📦 Install missing packages:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    return True

def check_ollama():
    """Check if Ollama is running and accessible."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            if models:
                print(f"✅ Ollama - Running ({len(models)} models available)")
                for model in models[:3]:  # Show first 3 models
                    print(f"   - {model['name']}")
                return True
            else:
                print("⚠️  Ollama - Running but no models found")
                print("   Run: ollama pull llama2")
                return False
        else:
            print("❌ Ollama - Not responding properly")
            return False
    except requests.exceptions.RequestException:
        print("❌ Ollama - Not running")
        print("   Install from: https://ollama.ai/")
        print("   Then run: ollama serve")
        return False

def check_environment():
    """Check environment configuration."""
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        print("   Copy env.example to .env and configure your settings")
        return False
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check required environment variables
    required_vars = ['TAVILY_API_KEY', 'MONGODB_URI']
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value or value == f"your_{var.lower()}_here":
            print(f"❌ {var} - Not configured")
            missing_vars.append(var)
        else:
            print(f"✅ {var} - Configured")
    
    if missing_vars:
        print(f"\n🔧 Configure missing environment variables in .env file")
        return False
    
    return True

def check_mongodb():
    """Check MongoDB connection."""
    try:
        from app.database import database
        import asyncio
        
        # Test connection
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(database.connect())
        loop.run_until_complete(database.disconnect())
        
        print("✅ MongoDB - Connected successfully")
        return True
    except Exception as e:
        print(f"❌ MongoDB - Connection failed: {e}")
        print("   Make sure MongoDB is running and MONGODB_URI is correct")
        return False

def check_tavily():
    """Check Tavily API access."""
    try:
        from app.config import settings
        import tavily
        
        client = tavily.TavilyClient(api_key=settings.tavily_api_key)
        # Simple test query
        response = client.search(query="AI policy", max_results=1)
        
        if response and 'results' in response:
            print("✅ Tavily API - Access confirmed")
            return True
        else:
            print("❌ Tavily API - Invalid response")
            return False
    except Exception as e:
        print(f"❌ Tavily API - Error: {e}")
        print("   Check your TAVILY_API_KEY in .env file")
        return False

def main():
    """Main startup check function."""
    print("🤖 AgentResearch - Startup Check")
    print("=" * 50)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Environment", check_environment),
        ("Ollama", check_ollama),
        ("MongoDB", check_mongodb),
        ("Tavily API", check_tavily),
    ]
    
    all_passed = True
    for name, check_func in checks:
        print(f"\n🔍 Checking {name}...")
        if not check_func():
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All checks passed! You can start the application:")
        print("   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        print("\n   Then visit: http://localhost:8000")
    else:
        print("⚠️  Some checks failed. Please fix the issues above before starting.")
        print("\n📚 Setup Guide:")
        print("   1. Install Python 3.9+")
        print("   2. Install dependencies: pip install -r requirements.txt")
        print("   3. Install Ollama: https://ollama.ai/")
        print("   4. Start Ollama: ollama serve")
        print("   5. Pull model: ollama pull llama2")
        print("   6. Copy env.example to .env and configure")
        print("   7. Get Tavily API key: https://tavily.com/")
        print("   8. Start MongoDB (local or Atlas)")
        print("   9. Run this script again to verify")

if __name__ == "__main__":
    main() 