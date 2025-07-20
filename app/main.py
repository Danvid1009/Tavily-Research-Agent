import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import aiofiles
import os

from .config import settings
from .database import database
from .api.routes import router as api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered tool for researching and comparing AI policy documents across jurisdictions",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")

# Mount static files
if os.path.exists("app/static"):
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    try:
        # Connect to database
        await database.connect()
        logger.info("Application started successfully")
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on application shutdown."""
    try:
        # Disconnect from database
        await database.disconnect()
        logger.info("Application shutdown completed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main application interface."""
    try:
        async with aiofiles.open("app/static/index.html", "r") as f:
            content = await f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>AgentResearch</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 800px; margin: 0 auto; }
                .header { text-align: center; margin-bottom: 40px; }
                .api-links { margin-top: 30px; }
                .api-links a { margin: 10px; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🤖 AgentResearch</h1>
                    <p>AI-powered tool for researching and comparing AI policy documents across jurisdictions</p>
                </div>
                
                <h2>Welcome to AgentResearch</h2>
                <p>This application uses a 4-agent workflow to automatically research, analyze, and compare AI policy documents from different countries/regions.</p>
                
                <h3>The 4-Agent Workflow:</h3>
                <ul>
                    <li><strong>🔍 Search Agent:</strong> Uses Tavily API to find relevant AI policy documents</li>
                    <li><strong>📄 Extract Agent:</strong> Uses Ollama to extract key legal clauses from documents</li>
                    <li><strong>⚖️ Compare Agent:</strong> Analyzes and compares clauses across jurisdictions</li>
                    <li><strong>📝 Summarize Agent:</strong> Generates executive summaries and recommendations</li>
                </ul>
                
                <div class="api-links">
                    <a href="/api/docs">API Documentation</a>
                    <a href="/api/research">Research API</a>
                </div>
                
                <h3>Example Query:</h3>
                <p>"Compare AI safety regulations in EU vs US"</p>
            </div>
        </body>
        </html>
        """)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test database connection
        await database.client.admin.command('ping')
        return {
            "status": "healthy",
            "app_name": settings.app_name,
            "version": settings.app_version,
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    ) 