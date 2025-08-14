from fastapi import FastAPI
from proxies.config import PROXY_MODULES
from proxies.module_loader import ModuleLoader

app = FastAPI(
    title="Proxy API Gateway",
    description="Dynamic proxy API gateway for multiple integrations",
    version="1.0.0"
)

# Initialize module loader
module_loader = ModuleLoader(PROXY_MODULES)

# Load all enabled modules
loaded_routers = module_loader.load_all_modules()

# Include all loaded routers
for module_name, router in loaded_routers.items():
    app.include_router(router)
    print(f"✅ Loaded module: {module_name}")

@app.get("/")
async def root():
    """Root endpoint showing loaded modules."""
    loaded_modules = list(loaded_routers.keys())
    return {
        "message": "Proxy API Gateway",
        "loaded_modules": loaded_modules,
        "total_modules": len(loaded_modules)
    }

@app.get("/modules")
async def list_modules():
    """List all configured modules and their status."""
    modules_info = {}
    
    for module_name, module_config in PROXY_MODULES.items():
        is_loaded = module_name in loaded_routers
        modules_info[module_name] = {
            "enabled": module_config.get("enabled", False),
            "loaded": is_loaded,
            "port": module_config.get("port"),
            "host": module_config.get("host")
        }
    
    return {
        "modules": modules_info,
        "total_configured": len(PROXY_MODULES),
        "total_loaded": len(loaded_routers)
    }

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "loaded_modules": len(loaded_routers),
        "modules": list(loaded_routers.keys())
    }