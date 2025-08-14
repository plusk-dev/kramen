"""
Module loader utility for dynamically importing proxy modules.
"""

import importlib
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter

logger = logging.getLogger(__name__)


class ModuleLoader:
    """Utility class for dynamically loading modules based on configuration."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the module loader with configuration.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary containing module settings
        """
        self.config = config
        self.loaded_modules = {}
    
    def load_module(self, module_name: str) -> Optional[APIRouter]:
        """
        Load a module dynamically based on the configuration.
        
        Args:
            module_name (str): Name of the module to load
            
        Returns:
            Optional[APIRouter]: The router from the loaded module, or None if loading failed
        """
        if module_name not in self.config:
            logger.warning(f"Module '{module_name}' not found in configuration")
            return None
        
        module_config = self.config[module_name]
        
        if not module_config.get("enabled", False):
            logger.info(f"Module '{module_name}' is disabled in configuration")
            return None
        
        try:
            # Import the module
            module_path = module_config["module_path"]
            module = importlib.import_module(module_path)
            
            # Get the router from the module
            router_name = module_config["router_name"]
            router = getattr(module, router_name, None)
            
            if router is None:
                logger.error(f"Router '{router_name}' not found in module '{module_path}'")
                return None
            
            self.loaded_modules[module_name] = {
                "module": module,
                "router": router,
                "config": module_config
            }
            
            logger.info(f"Successfully loaded module '{module_name}'")
            return router
            
        except ImportError as e:
            logger.error(f"Failed to import module '{module_path}': {e}")
            return None
        except AttributeError as e:
            logger.error(f"Failed to get router '{router_name}' from module '{module_path}': {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error loading module '{module_name}': {e}")
            return None
    
    def load_all_modules(self) -> Dict[str, APIRouter]:
        """
        Load all enabled modules from the configuration.
        
        Returns:
            Dict[str, APIRouter]: Dictionary mapping module names to their routers
        """
        routers = {}
        
        for module_name in self.config:
            router = self.load_module(module_name)
            if router:
                routers[module_name] = router
        
        return routers
    
    def get_module_config(self, module_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the configuration for a specific module.
        
        Args:
            module_name (str): Name of the module
            
        Returns:
            Optional[Dict[str, Any]]: Module configuration or None if not found
        """
        return self.config.get(module_name)
    
    def get_loaded_modules(self) -> Dict[str, Any]:
        """
        Get information about all loaded modules.
        
        Returns:
            Dict[str, Any]: Dictionary containing loaded module information
        """
        return self.loaded_modules.copy() 