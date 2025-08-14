#!/usr/bin/env python3
"""
Health check script for Kramen Backend

This script checks the health of all services and dependencies.
"""

import asyncio
import os
import sys
import time
from pathlib import Path

# Add parent directory to path to import modules
sys.path.append(str(Path(__file__).parent.parent))

try:
    import requests
    import redis
    from qdrant_client import QdrantClient
    from config import REDIS_URL, QDRANT_URL, QDRANT_API_KEY
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please run: pip install -r requirements.txt")
    sys.exit(1)


class HealthChecker:
    """Health checker for all services."""
    
    def __init__(self):
        self.checks = {
            "Redis": self.check_redis,
            "Qdrant": self.check_qdrant,
            "Main API": self.check_main_api,
            "Environment": self.check_environment,
        }
    
    def check_redis(self):
        """Check Redis connection."""
        try:
            r = redis.from_url(REDIS_URL)
            r.ping()
            return True, "Connected successfully"
        except Exception as e:
            return False, str(e)
    
    def check_qdrant(self):
        """Check Qdrant connection."""
        try:
            client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
            collections = client.get_collections()
            return True, f"Connected, {len(collections.collections)} collections"
        except Exception as e:
            return False, str(e)
    
    def check_main_api(self):
        """Check main API server."""
        try:
            response = requests.get("http://localhost:5000/docs", timeout=5)
            if response.status_code == 200:
                return True, "API server responding"
            else:
                return False, f"HTTP {response.status_code}"
        except requests.ConnectionError:
            return False, "API server not running"
        except Exception as e:
            return False, str(e)
    
    def check_environment(self):
        """Check environment configuration."""
        required_vars = [
            "OPENAI_API_KEY",
            "GOOGLE_CLIENT_ID",
            "GOOGLE_CLIENT_SECRET"
        ]
        
        missing = []
        for var in required_vars:
            if not os.getenv(var):
                missing.append(var)
        
        if missing:
            return False, f"Missing: {', '.join(missing)}"
        return True, "All required variables set"
    
    def run_all_checks(self):
        """Run all health checks."""
        print("🏥 Kramen Backend Health Check")
        print("=" * 40)
        
        all_healthy = True
        
        for service, check_func in self.checks.items():
            print(f"Checking {service}...", end=" ")
            try:
                healthy, message = check_func()
                if healthy:
                    print(f"✅ {message}")
                else:
                    print(f"❌ {message}")
                    all_healthy = False
            except Exception as e:
                print(f"❌ Error: {e}")
                all_healthy = False
        
        print("=" * 40)
        if all_healthy:
            print("✅ All services healthy!")
            return 0
        else:
            print("❌ Some services have issues")
            return 1


def main():
    """Main function."""
    checker = HealthChecker()
    exit_code = checker.run_all_checks()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
