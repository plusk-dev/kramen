"""
Server module for running individual proxy modules on specific ports.
"""

import asyncio
import logging
import uvicorn
from typing import Dict, Any, Optional
from fastapi import FastAPI
from proxies.module_loader import ModuleLoader
from proxies.config import PROXY_MODULES, DEFAULT_CONFIG

logger = logging.getLogger(__name__)


class ProxyServer:
    """Server class for running proxy modules on specific ports."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the proxy server.
        
        Args:
            config (Dict[str, Any], optional): Configuration for modules. Defaults to PROXY_MODULES.
        """
        self.config = config or PROXY_MODULES
        self.module_loader = ModuleLoader(self.config)
        self.servers = {}
    
    def create_app_for_module(self, module_name: str) -> Optional[FastAPI]:
        """
        Create a FastAPI app for a specific module.
        
        Args:
            module_name (str): Name of the module
            
        Returns:
            Optional[FastAPI]: FastAPI app instance or None if module loading failed
        """
        router = self.module_loader.load_module(module_name)
        if not router:
            return None
        
        app = FastAPI(
            title=f"{module_name.title()} Proxy API",
            description=f"Proxy API for {module_name} integration",
            version="1.0.0"
        )
        
        app.include_router(router)
        
        @app.get("/")
        async def root():
            return {
                "message": f"Hello from {module_name.title()} Proxy",
                "module": module_name,
                "status": "running"
            }
        
        @app.get("/health")
        async def health():
            return {"status": "healthy", "module": module_name}
        
        return app
    
    async def start_module_server(self, module_name: str) -> bool:
        """
        Start a server for a specific module.
        
        Args:
            module_name (str): Name of the module to start
            
        Returns:
            bool: True if server started successfully, False otherwise
        """
        if module_name not in self.config:
            logger.error(f"Module '{module_name}' not found in configuration")
            return False
        
        module_config = self.config[module_name]
        
        if not module_config.get("enabled", False):
            logger.info(f"Module '{module_name}' is disabled")
            return False
        
        app = self.create_app_for_module(module_name)
        if not app:
            logger.error(f"Failed to create app for module '{module_name}'")
            return False
        
        host = module_config.get("host", DEFAULT_CONFIG["host"])
        port = module_config.get("port", DEFAULT_CONFIG["port"])
        
        try:
            config = uvicorn.Config(
                app=app,
                host=host,
                port=port,
                log_level="info",
                reload=False,  # Disable reload for proxy servers
                access_log=False  # Disable access logs to reduce noise
            )
            
            server = uvicorn.Server(config)
            self.servers[module_name] = server
            
            logger.info(f"Starting server for module '{module_name}' on {host}:{port}")
            
            # Start the server in a separate task
            task = asyncio.create_task(server.serve())
            self.servers[module_name] = {"server": server, "task": task}
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start server for module '{module_name}': {e}")
            return False
    
    async def start_all_servers(self) -> Dict[str, bool]:
        """
        Start servers for all enabled modules.
        
        Returns:
            Dict[str, bool]: Dictionary mapping module names to success status
        """
        results = {}
        
        for module_name in self.config:
            success = await self.start_module_server(module_name)
            results[module_name] = success
        
        return results
    
    async def stop_server(self, module_name: str) -> bool:
        """
        Stop a specific module server.
        
        Args:
            module_name (str): Name of the module to stop
            
        Returns:
            bool: True if server stopped successfully, False otherwise
        """
        if module_name not in self.servers:
            logger.warning(f"Server for module '{module_name}' not found")
            return False
        
        try:
            server_info = self.servers[module_name]
            server = server_info["server"]
            task = server_info["task"]
            
            # Stop the server
            server.should_exit = True
            
            # Cancel the task if it's still running
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            del self.servers[module_name]
            logger.info(f"Stopped server for module '{module_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to stop server for module '{module_name}': {e}")
            return False
    
    async def stop_all_servers(self) -> Dict[str, bool]:
        """
        Stop all running servers.
        
        Returns:
            Dict[str, bool]: Dictionary mapping module names to stop success status
        """
        results = {}
        
        for module_name in list(self.servers.keys()):
            success = await self.stop_server(module_name)
            results[module_name] = success
        
        return results
    
    def get_running_servers(self) -> Dict[str, Any]:
        """
        Get information about running servers.
        
        Returns:
            Dict[str, Any]: Dictionary containing running server information
        """
        return {
            module_name: {
                "config": self.config[module_name],
                "status": "running"
            }
            for module_name in self.servers
        }


async def main():
    """Main function to start all proxy servers."""
    server = ProxyServer()
    
    try:
        results = await server.start_all_servers()
        
        # Log results
        for module_name, success in results.items():
            if success:
                config = server.config[module_name]
                logger.info(f"✅ {module_name} server started on {config['host']}:{config['port']}")
            else:
                logger.error(f"❌ Failed to start {module_name} server")
        
        # Keep the main task running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down servers...")
        await server.stop_all_servers()
        logger.info("All servers stopped")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main()) 