#!/usr/bin/env python3
"""
Setup script for Kramen Backend

This script helps with initial setup and configuration of the project.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def check_python_version():
    """Check if Python version is 3.8 or higher."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required.")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python version: {sys.version}")


def check_external_services():
    """Check if external services are available."""
    services = {
        "Redis": ("redis-cli", "ping"),
        "Qdrant": ("curl", "-s", "http://localhost:6333/")
    }
    
    for service_name, command in services.items():
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=5)
            if service_name == "Redis" and "PONG" in result.stdout:
                print(f"✅ {service_name} is running")
            elif service_name == "Qdrant" and result.returncode == 0:
                print(f"✅ {service_name} is running")
            else:
                print(f"⚠️  {service_name} may not be running properly")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print(f"❌ {service_name} is not accessible")


def create_env_file():
    """Create .env file from template if it doesn't exist."""
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ Created .env file from template")
        print("⚠️  Please edit .env file with your actual API keys and configuration")
    elif env_file.exists():
        print("✅ .env file already exists")
    else:
        print("❌ env.example file not found")


def install_dependencies():
    """Install Python dependencies."""
    try:
        print("📦 Installing Python dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True)
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        sys.exit(1)


def setup_database():
    """Initialize database if needed."""
    from models import Base, engine
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database setup failed: {e}")


def main():
    """Main setup function."""
    print("🚀 Setting up Kramen Backend...")
    print("=" * 50)
    
    check_python_version()
    create_env_file()
    install_dependencies()
    
    print("\n🔍 Checking external services...")
    check_external_services()
    
    print("\n💾 Setting up database...")
    setup_database()
    
    print("\n" + "=" * 50)
    print("✅ Setup completed!")
    print("\n📚 Next steps:")
    print("1. Edit .env file with your API keys")
    print("2. Start external services (Redis, Qdrant)")
    print("3. Run: uvicorn main:app --reload")
    print("\n📖 Check README.md for detailed instructions")


if __name__ == "__main__":
    main()
