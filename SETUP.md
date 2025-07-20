# AgentResearch Setup Guide

This guide will help you set up and run the AgentResearch application, an AI-powered tool for researching and comparing AI policy documents across jurisdictions.

## 🎯 What You'll Build

AgentResearch uses a 4-agent workflow to automatically:
1. **Search** for AI policy documents using Tavily API
2. **Extract** key legal clauses using Ollama (local LLM)
3. **Compare** regulatory approaches across jurisdictions
4. **Summarize** findings and generate recommendations

## 📋 Prerequisites

Before you begin, ensure you have:

- **Python 3.9 or higher**
- **Git** (for cloning the repository)
- **Internet connection** (for API access and model downloads)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd Tavily_Agent

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Install Ollama

Ollama is required for local LLM processing. Install it from [ollama.ai](https://ollama.ai/):

```bash
# macOS/Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# Download from https://ollama.ai/download/windows

# Start Ollama
ollama serve

# Pull the required model (in a new terminal)
ollama pull llama2
```

### 3. Get API Keys

#### Tavily API Key
1. Visit [tavily.com](https://tavily.com/)
2. Sign up for a free account
3. Get your API key from the dashboard

#### MongoDB (Optional)
- **Local MongoDB**: Install and run locally
- **MongoDB Atlas**: Create a free cluster at [mongodb.com](https://mongodb.com/)

### 4. Configure Environment

```bash
# Copy the example environment file
cp env.example .env

# Edit .env with your settings
nano .env  # or use your preferred editor
```

Configure the following in your `.env` file:

```env
# Required: Your Tavily API key
TAVILY_API_KEY=your_actual_tavily_api_key_here

# Required: MongoDB connection string
MONGODB_URI=mongodb://localhost:27017
# Or for MongoDB Atlas:
# MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/database

# Optional: Database name
DATABASE_NAME=agent_research

# Optional: Ollama settings (defaults shown)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Optional: Debug mode
DEBUG=False
```

### 5. Verify Setup

Run the startup check script to verify everything is configured correctly:

```bash
python start.py
```

This script will check:
- ✅ Python version compatibility
- ✅ Required dependencies
- ✅ Environment configuration
- ✅ Ollama availability
- ✅ MongoDB connection
- ✅ Tavily API access

### 6. Start the Application

```bash
# Start the FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Access the Application

Open your browser and navigate to:
- **Main Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs
- **Health Check**: http://localhost:8000/health

## 🔧 Detailed Configuration

### Ollama Models

The application is configured to use `llama2` by default. You can use other models:

```bash
# Pull alternative models
ollama pull llama2:7b
ollama pull llama2:13b
ollama pull codellama
ollama pull mistral

# Update .env to use a different model
OLLAMA_MODEL=llama2:13b
```

### MongoDB Setup

#### Local MongoDB

```bash
# macOS (using Homebrew)
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb/brew/mongodb-community

# Ubuntu/Debian
sudo apt-get install mongodb
sudo systemctl start mongodb

# Windows
# Download and install from mongodb.com
```

#### MongoDB Atlas (Cloud)

1. Create account at [mongodb.com](https://mongodb.com/)
2. Create a new cluster (free tier available)
3. Create a database user
4. Get your connection string
5. Update `MONGODB_URI` in `.env`

### Tavily API Configuration

The search agent is configured to focus on academic and legal sources. You can modify search parameters in `app/agents/search_agent.py`:

```python
# Example: Add more domains to search
"include_domains": [
    "europa.eu", "ec.europa.eu", "whitehouse.gov", "congress.gov",
    "gov.uk", "parliament.uk", "oecd.org", "un.org", "wto.org",
    "academic.oup.com", "springer.com", "ieee.org", "arxiv.org",
    "your-additional-domain.com"  # Add your preferred sources
]
```

## 🧪 Testing the Application

### 1. Submit a Test Query

Use the web interface or API to submit a research query:

**Example Query**: "Compare AI safety regulations in EU vs US"

**API Call**:
```bash
curl -X POST "http://localhost:8000/api/research" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Compare AI safety regulations in EU vs US",
    "regions": ["EU", "US"],
    "document_types": ["legislation", "policy_framework"],
    "max_documents": 10
  }'
```

### 2. Monitor Progress

Check the status of your research:

```bash
# Replace QUERY_ID with the ID returned from the submit call
curl "http://localhost:8000/api/research/QUERY_ID/status"
```

### 3. Get Results

Retrieve the completed research:

```bash
curl "http://localhost:8000/api/research/QUERY_ID"
```

## 🐛 Troubleshooting

### Common Issues

#### Ollama Not Running
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if not running
ollama serve
```

#### MongoDB Connection Issues
```bash
# Test MongoDB connection
mongosh "your_connection_string"

# Check if MongoDB is running
sudo systemctl status mongodb  # Linux
brew services list | grep mongodb  # macOS
```

#### Tavily API Errors
- Verify your API key is correct
- Check your Tavily account status
- Ensure you have sufficient credits

#### Python Dependencies
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check for conflicts
pip check
```

### Logs and Debugging

Enable debug mode in `.env`:
```env
DEBUG=True
```

Check application logs:
```bash
# View real-time logs
tail -f logs/app.log

# Check system resources
htop  # or top
```

## 📊 Performance Optimization

### For Production Use

1. **Use a Production Ollama Model**:
   ```bash
   ollama pull llama2:70b  # Larger, more capable model
   ```

2. **Configure MongoDB Indexes**:
   ```javascript
   // In MongoDB shell
   db.research_queries.createIndex({"created_at": -1})
   db.research_results.createIndex({"query": "text"})
   ```

3. **Adjust Agent Parameters**:
   - Modify `max_documents` in queries
   - Adjust `max_extraction_length` in config
   - Tune Ollama parameters in agent files

4. **Use a Reverse Proxy**:
   ```bash
   # Example with nginx
   sudo apt-get install nginx
   # Configure nginx to proxy to localhost:8000
   ```

## 🔒 Security Considerations

1. **Environment Variables**: Never commit `.env` files
2. **API Keys**: Rotate Tavily API keys regularly
3. **Database**: Use strong passwords for MongoDB
4. **Network**: Configure firewalls appropriately
5. **Updates**: Keep dependencies updated

## 📈 Scaling

### Horizontal Scaling
- Run multiple application instances
- Use a load balancer
- Configure MongoDB replica sets

### Vertical Scaling
- Increase server resources
- Use more powerful Ollama models
- Optimize database queries

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

- **Issues**: Create an issue in the GitHub repository
- **Documentation**: Check the README.md file
- **API Docs**: Visit http://localhost:8000/api/docs

## 🎉 You're Ready!

Your AgentResearch application is now set up and ready to analyze AI policy documents across jurisdictions. Start by submitting your first research query and watch the 4-agent workflow in action! 