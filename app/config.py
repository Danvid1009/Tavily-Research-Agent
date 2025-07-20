import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    """Application settings and configuration."""
    
    # API Keys
    tavily_api_key: str = os.getenv("TAVILY_API_KEY", "")
    
    # Database
    mongodb_uri: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    database_name: str = os.getenv("DATABASE_NAME", "agent_research")
    
    # Ollama Configuration
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama2")
    
    # Application Settings
    app_name: str = "AgentResearch"
    app_version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Search Configuration
    max_search_results: int = 20
    search_timeout: int = 30
    
    # Agent Configuration
    max_extraction_length: int = 4000
    comparison_batch_size: int = 5
    
    class Config:
        env_file = ".env"

settings = Settings() 