"""
Configuration file for proxy modules.
This file declares which modules in the apps directory should be loaded and on which ports.
"""

# Configuration for proxy modules
PROXY_MODULES = {
    "linear": {
        "enabled": True,
        "port": 8001,
        "host": "0.0.0.0",
        "module_path": "proxies.apps.linear.main",
        "router_name": "linear_router"
    },
    "stripe": {
        "enabled": False,  # Set to True when stripe module is implemented
        "port": 8002,
        "host": "0.0.0.0",
        "module_path": "proxies.apps.stripe.main",
        "router_name": "stripe_router"
    },
    "google_calendar": {
        "enabled": True,
        "port": 8003,
        "host": "0.0.0.0",
        "module_path": "proxies.apps.google_calendar.main",
        "router_name": "google_calendar_router"
    }
    # Add more modules here as needed
}

# Default configuration
DEFAULT_CONFIG = {
    "host": "0.0.0.0",
    "port": 8000,
    "debug": False,
    "reload": False
} 