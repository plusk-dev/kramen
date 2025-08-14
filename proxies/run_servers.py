#!/usr/bin/env python3
"""
Script to run individual proxy servers on their configured ports.
This allows each module to run independently on its own port.
"""

import asyncio
import logging
import sys
import argparse
from proxies.server import ProxyServer
from proxies.config import PROXY_MODULES

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_single_module(module_name: str):
    """Run a single module on its configured port."""
    if module_name not in PROXY_MODULES:
        logger.error(f"Module '{module_name}' not found in configuration")
        return False
    
    module_config = PROXY_MODULES[module_name]
    
    if not module_config.get("enabled", False):
        logger.error(f"Module '{module_name}' is disabled in configuration")
        return False
    
    server = ProxyServer()
    
    try:
        success = await server.start_module_server(module_name)
        if success:
            logger.info(f"✅ {module_name} server started successfully")
            logger.info(f"🌐 Server running on {module_config['host']}:{module_config['port']}")
            
            # Keep the server running
            while True:
                await asyncio.sleep(1)
        else:
            logger.error(f"❌ Failed to start {module_name} server")
            return False
            
    except KeyboardInterrupt:
        logger.info(f"🛑 Stopping {module_name} server...")
        await server.stop_server(module_name)
        logger.info(f"✅ {module_name} server stopped")
        return True
    except Exception as e:
        logger.error(f"❌ Error running {module_name} server: {e}")
        return False


async def run_all_modules():
    """Run all enabled modules on their configured ports."""
    server = ProxyServer()
    
    try:
        results = await server.start_all_servers()
        
        # Log results
        started_modules = []
        for module_name, success in results.items():
            if success:
                config = server.config[module_name]
                started_modules.append(module_name)
                logger.info(f"✅ {module_name} server started on {config['host']}:{config['port']}")
            else:
                logger.error(f"❌ Failed to start {module_name} server")
        
        if not started_modules:
            logger.error("❌ No modules were started successfully")
            return False
        
        logger.info(f"🚀 All servers started successfully: {', '.join(started_modules)}")
        
        # Keep all servers running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down all servers...")
        await server.stop_all_servers()
        logger.info("✅ All servers stopped")
        return True
    except Exception as e:
        logger.error(f"❌ Error running servers: {e}")
        return False


def list_modules():
    """List all configured modules and their status."""
    print("\n📋 Configured Modules:")
    print("=" * 50)
    
    for module_name, config in PROXY_MODULES.items():
        status = "✅ Enabled" if config.get("enabled", False) else "❌ Disabled"
        port = config.get("port", "N/A")
        host = config.get("host", "N/A")
        
        print(f"• {module_name}:")
        print(f"  Status: {status}")
        print(f"  Host: {host}")
        print(f"  Port: {port}")
        print()


def main():
    """Main function to handle command line arguments and run servers."""
    parser = argparse.ArgumentParser(
        description="Run proxy servers for configured modules",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m proxies.run_servers --all                    # Run all enabled modules
  python -m proxies.run_servers --module linear          # Run only linear module
  python -m proxies.run_servers --list                   # List all configured modules
        """
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all enabled modules on their configured ports"
    )
    
    parser.add_argument(
        "--module",
        type=str,
        help="Run a specific module by name"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all configured modules and their status"
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_modules()
        return
    
    if args.all:
        logger.info("🚀 Starting all enabled modules...")
        success = asyncio.run(run_all_modules())
        sys.exit(0 if success else 1)
    
    elif args.module:
        logger.info(f"🚀 Starting {args.module} module...")
        success = asyncio.run(run_single_module(args.module))
        sys.exit(0 if success else 1)
    
    else:
        # Default behavior: run all modules
        logger.info("🚀 Starting all enabled modules...")
        success = asyncio.run(run_all_modules())
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 