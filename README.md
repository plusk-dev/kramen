# Kramen

Kramen makes it easy for language models to use many different tools and APIs at once. It connects LLMs to third-party services using tool calling and Retrieval-Augmented Generation (RAG), so you can handle complex tasks with simple queries. Proxies are used to provide isolated, scalable access to each integration.


To make integrations, you make a proxy to another API. This proxy serves as a simpler API that is easier for LLMs to interpret. The OpenAPI spec of that API serves as the documentation of tools. This can be upserted into the vector database (Qdrant) via `/integrations/upload-openapi`

## Getting Started with the UI

To set up the user interface, make sure to install and run the frontend. The frontend code is located in the `frontend/` directory. Follow the instructions in the `frontend/README.md` to install dependencies and start the development server.


## Proxy Configuration

The proxy system provides isolated endpoints for different third-party integrations. Each integration runs as an independent FastAPI application on its own port.

### Proxy Module Configuration

Configure proxy modules in `proxies/config.py`:

```python
PROXY_MODULES = {
    "linear": {
        "enabled": True,
        "port": 8001,
        "host": "0.0.0.0",
        "module_path": "apps.linear.main",
        "router_name": "linear_router"
    },
    "google_calendar": {
        "enabled": True,
        "port": 8002,
        "host": "0.0.0.0",
        "module_path": "apps.google_calendar.main",
        "router_name": "calendar_router"
    }
}
```

### Creating a New Integration Proxy

To create a new integration proxy, follow this structured approach:

1. **Create the module directory structure**:
```
proxies/apps/your_integration/
├── __init__.py
├── main.py              # FastAPI router with endpoints
├── client/
│   ├── __init__.py
│   └── client.py        # API client for the third-party service
└── schemas/
    ├── __init__.py
    └── schemas.py       # Pydantic models for requests/responses
```

2. **Implement the API client** (`client/client.py`):
```python
import httpx
from typing import Dict, Any

class YourIntegrationClient:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def get_data(self, endpoint: str, params: Dict[str, Any] = None):
        headers = {"Authorization": f"Bearer {self.api_key}"}
        response = await self.client.get(
            f"{self.base_url}/{endpoint}",
            headers=headers,
            params=params
        )
        return response.json()
    
    async def post_data(self, endpoint: str, data: Dict[str, Any]):
        headers = {"Authorization": f"Bearer {self.api_key}"}
        response = await self.client.post(
            f"{self.base_url}/{endpoint}",
            headers=headers,
            json=data
        )
        return response.json()
```

3. **Define Pydantic schemas** (`schemas/schemas.py`):
```python
from pydantic import BaseModel
from typing import Optional, List

class CreateItemRequest(BaseModel):
    title: str
    description: Optional[str] = None
    tags: List[str] = []

class ItemResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    created_at: str
    updated_at: str
```

4. **Implement the FastAPI router** (`main.py`):
```python
from fastapi import APIRouter, HTTPException, Header, Depends
from typing import Optional, List
from .client.client import YourIntegrationClient
from .schemas.schemas import CreateItemRequest, ItemResponse

your_integration_router = APIRouter(
    prefix="/your-integration",
    tags=["Your Integration"]
)

def get_client(authorization: str = Header(...)):
    # Parse authorization header and create client
    api_key = authorization.replace("Bearer ", "")
    return YourIntegrationClient(
        api_key=api_key,
        base_url="https://api.yourintegration.com"
    )

@your_integration_router.get("/items", response_model=List[ItemResponse])
async def get_items(client: YourIntegrationClient = Depends(get_client)):
    try:
        items = await client.get_data("items")
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@your_integration_router.post("/items", response_model=ItemResponse)
async def create_item(
    item: CreateItemRequest,
    client: YourIntegrationClient = Depends(get_client)
):
    try:
        result = await client.post_data("items", item.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

5. **Add to proxy configuration**:
Add your integration to `proxies/config.py`:
```python
"your_integration": {
    "enabled": True,
    "port": 8003,  # Choose an available port
    "host": "0.0.0.0",
    "module_path": "apps.your_integration.main",
    "router_name": "your_integration_router"
}
```

6. **Test the integration**:
```bash
# List all configured modules
python -m proxies.run_servers --list

# Start your specific integration
python -m proxies.run_servers --module your_integration

# Or start all integrations
python -m proxies.run_servers --all
```

### Authentication Handling

For integrations requiring authentication, implement header-based auth:

```python
from fastapi import Header, HTTPException
import json

def parse_auth_header(x_auth: str = Header(...)):
    try:
        auth_data = json.loads(x_auth)
        return auth_data
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid X-Auth header")

@your_integration_router.get("/protected-endpoint")
async def protected_endpoint(auth_data: dict = Depends(parse_auth_header)):
    # Use auth_data to authenticate with the third-party API
    client = YourIntegrationClient(
        api_key=auth_data.get("api_key"),
        base_url=auth_data.get("base_url", "https://api.default.com")
    )
    return await client.get_data("protected-resource")
```

## Installation

### Prerequisites

- Python 3.8 or higher
- Redis server (6.0+)
- Qdrant vector database (1.0+)

### Environment Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd kramen-backend
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp env.example .env
```

Edit the `.env` file with your configuration:

```bash
# Database Configuration
DATABASE_URL=sqlite:///dev.db

# Cache Layer
REDIS_URL=redis://localhost:6379

# Vector Database
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

# AI Model Configuration
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GOOGLE_API_KEY=your_google_key

# Google OAuth
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_PROJECT_ID=your_project_id
GOOGLE_REDIRECT_URI=http://localhost:5173/callback
```

5. Initialize the database:
```bash
python -c "from models import Base, engine; Base.metadata.create_all(bind=engine)"
```

## Usage

### Starting the Main Application

```bash
uvicorn main:app --reload --port 5000
```

The API will be available at `http://localhost:5000` with interactive documentation at `http://localhost:5000/docs`.

### Proxy Server Management

Start all configured proxy servers:
```bash
python -m proxies.run_servers --all
```

Start a specific proxy module:
```bash
python -m proxies.run_servers --module linear
```

List available modules:
```bash
python -m proxies.run_servers --list
```

## Query Processing

The system processes natural language queries through a multi-stage RAG pipeline that automatically selects appropriate integrations and executes API calls.

### Query Execution

```bash
curl -X POST "http://localhost:5000/run/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Get my Linear issues from this week",
    "user_context": {
      "integrations": ["linear"],
      "auth_data": {"api_key": "your_linear_key"}
    }
  }'
```

### Query Processing Pipeline

1. **Query Decomposition**: Break down complex queries into actionable components
2. **Integration Selection**: Choose appropriate integrations based on query intent
3. **Endpoint Filtering**: Identify relevant API endpoints for the query
4. **Request Generation**: Create properly formatted API requests
5. **Response Synthesis**: Combine results into coherent responses

## OAuth Setup

### Google OAuth Configuration

Configure Google Calendar integration:
```bash
python -m utils.google_auth
```

This will guide you through the OAuth flow and generate the necessary authentication tokens.

## API Documentation

### Integration Management Endpoints

**POST** `/integrations/create`
- Create new third-party integration
- Requires integration name, description, and authentication structure

**GET** `/integrations/all`
- Retrieve all configured integrations
- Returns integration metadata and status

**DELETE** `/integrations/delete`
- Remove integration configuration
- Cascades to associated endpoints and data

**POST** `/integrations/upload-openapi`
- Upload OpenAPI specification for integration
- Automatically processes endpoints and schemas

### Query Processing Endpoints

**POST** `/run/query`
- Execute AI-powered query against configured integrations
- Supports natural language query processing
- Returns structured response with source attribution

**GET** `/run/endpoints`
- List available API endpoints across all integrations
- Includes endpoint metadata and parameter specifications

### Proxy Endpoints

Each proxy module operates on its configured port:
- Linear: `http://localhost:8001`
- Google Calendar: `http://localhost:8002`

## Configuration

### Embedding Model Configuration

The system supports multiple embedding approaches:

- **Dense Embeddings**: `sentence-transformers/all-MiniLM-L6-v2`
- **Sparse Embeddings**: `Qdrant/bm25`
- **Late Interaction**: `colbert-ir/colbertv2.0`

Configure models in `config.py`:

```python
DENSE_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
SPARSE_EMBEDDING_MODEL = "bm25"
LATE_EMBEDDING_MODEL = "colbertv2.0"
```

### LLM Provider Configuration

The system supports multiple language model providers through the DSPy framework:

```python
LLM_API_KEYS = {
    "openai/gpt-4.1": os.getenv("OPENAI_API_KEY"),
    "claude-3-sonnet": os.getenv("ANTHROPIC_API_KEY"),
    "google/gemini-pro": os.getenv("GOOGLE_API_KEY"),
}
```

## Development

### Project Structure

```
kramen-backend/
├── main.py                 # Main FastAPI application
├── config.py              # System configuration
├── models.py              # Database models
├── exception_handler.py   # Global exception handling
├── requirements.txt       # Python dependencies
├── proxies/               # Proxy system
│   ├── main.py           # Proxy gateway application
│   ├── config.py         # Proxy configuration
│   ├── run_servers.py    # Server management utility
│   ├── module_loader.py  # Dynamic module loading
│   └── apps/             # Integration modules
│       ├── linear/       # Linear integration
│       ├── google_calendar/ # Google Calendar integration
│       └── stripe/       # Stripe integration (development)
├── rag/                  # RAG processing system
│   ├── query.py         # Query processing logic
│   ├── identify_endpoints.py # Endpoint identification
│   ├── agents/          # AI processing agents
│   └── services/        # Core RAG services
├── utils/               # Shared utilities
│   ├── google_auth.py   # Google OAuth utilities
│   ├── general.py       # General utility functions
│   ├── openapi.py       # OpenAPI processing
│   ├── upsert.py        # Vector database operations
│   └── notifs/          # Notification services
└── schemas/             # Pydantic model definitions
    ├── dungo_schemas/   # Integration schemas
    └── raapi_schemas/   # RAG system schemas
```



### Testing

Health check utility:
```bash
python scripts/health_check.py
```

System setup verification:
```bash
python scripts/setup.py
```

## Dependencies

### Core Dependencies
- **FastAPI**: Web framework for API development
- **SQLAlchemy**: Database ORM and migrations
- **Qdrant Client**: Vector database connectivity
- **Redis**: Caching and session management
- **DSPy**: AI agent framework and LLM integration

### AI/ML Dependencies
- **FastEmbed**: Embedding model integration
- **LiteLLM**: Multi-provider LLM access
- **Sentence Transformers**: Dense embedding models
- **Transformers**: Advanced NLP capabilities

### Integration Dependencies
- **Google Auth**: OAuth 2.0 flow implementation
- **Stripe**: Payment processing integration
- **Requests**: HTTP client for API communication

## Security Considerations

- All sensitive configuration through environment variables
- OAuth 2.0 implementation for secure authentication
- API key management with provider-specific handling
- Input validation through Pydantic schemas
- CORS configuration for cross-origin security

## Performance Optimization

- Redis caching for frequently accessed data
- Vector database indexing for fast semantic search
- Lazy loading of embedding models
- Connection pooling for database operations
- Asynchronous request handling throughout the stack

## Monitoring and Logging

- Comprehensive logging throughout the application
- Health check endpoints for service monitoring
- Discord webhook integration for operational alerts
- Performance metrics collection
- Error tracking and aggregation

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.