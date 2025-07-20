# AgentResearch: AI Policy Analysis Tool

An AI-powered tool that automatically researches, analyzes, and compares AI policy documents from different countries/regions to help policymakers, researchers, and legal professionals understand how different jurisdictions approach AI regulation.

## 🎯 Main Purpose

AgentResearch helps users understand AI policy differences across jurisdictions by:
- Automatically searching for relevant policy documents
- Extracting key legal clauses and provisions
- Comparing regulatory approaches across regions
- Generating actionable insights and recommendations

## 🤖 The 4-Agent Workflow

### 🔍 Search Agent
- Uses the Tavily API to search for AI policy documents
- Searches for legal documents, regulations, and policy frameworks
- Focuses on specific regions (EU, US, etc.) based on your query

### 📄 Extract Agent
- Uses Ollama (local LLM) to extract key legal clauses from the documents
- Identifies important regulatory provisions, requirements, and restrictions
- Parses complex legal language into structured data

### ⚖️ Compare Agent
- Analyzes and compares the extracted clauses across different jurisdictions
- Identifies similarities, differences, and gaps in regulation
- Highlights key policy differences and their implications

### 📝 Summarize Agent
- Generates executive summaries of the comparisons
- Creates actionable insights for policymakers
- Provides recommendations based on the analysis

## 🚀 Example Use Case

**Query:** "Compare AI safety regulations in EU vs US"

**The app will:**
1. Search for EU AI Act documents and US AI policy documents
2. Extract key safety clauses from both
3. Compare requirements, enforcement mechanisms, and scope
4. Generate a summary showing differences like:
   - EU has stricter requirements for high-risk AI systems
   - US takes a more voluntary approach
   - Different definitions of "AI system"
   - Varying enforcement penalties

## 🏗️ Technical Architecture

- **Frontend:** Modern web interface for submitting queries and viewing results
- **Backend:** FastAPI with async processing
- **AI Models:** Ollama (local LLM) for analysis, Tavily for document search
- **Database:** MongoDB Atlas for storing research results
- **Workflow:** LangGraph for orchestrating the 4 agents

## 📋 Prerequisites

1. **Python 3.9+**
2. **Ollama** installed and running locally
3. **MongoDB Atlas** account (or local MongoDB)
4. **Tavily API** key

## 🛠️ Setup Instructions

### 1. Clone and Install Dependencies
```bash
git clone <repository-url>
cd Tavily_Agent
pip install -r requirements.txt
```

### 2. Environment Configuration
Create a `.env` file in the root directory:
```env
TAVILY_API_KEY=your_tavily_api_key
MONGODB_URI=your_mongodb_atlas_connection_string
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

### 3. Start Ollama
```bash
# Install and start Ollama (if not already running)
ollama serve
ollama pull llama2
```

### 4. Run the Application
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Access the Application
Open your browser and navigate to `http://localhost:8000`

## 📁 Project Structure

```
Tavily_Agent/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py              # Configuration settings
│   ├── database.py            # MongoDB connection
│   ├── models/                # Pydantic models
│   │   ├── __init__.py
│   │   ├── query.py
│   │   └── response.py
│   ├── agents/                # The 4 AI agents
│   │   ├── __init__.py
│   │   ├── search_agent.py
│   │   ├── extract_agent.py
│   │   ├── compare_agent.py
│   │   └── summarize_agent.py
│   ├── workflow/              # LangGraph workflow
│   │   ├── __init__.py
│   │   └── research_workflow.py
│   ├── api/                   # API routes
│   │   ├── __init__.py
│   │   └── routes.py
│   └── static/                # Frontend assets
│       ├── css/
│       ├── js/
│       └── index.html
├── requirements.txt
├── .env.example
└── README.md
```

## 🔧 Configuration

### Ollama Models
The application is configured to use `llama2` by default. You can change this in the `.env` file:
```env
OLLAMA_MODEL=llama2
```

### Tavily Search Configuration
The search agent is configured to focus on academic and legal sources. You can modify search parameters in `app/agents/search_agent.py`.

## 🚀 Usage

1. **Submit a Query:** Enter your research question in the web interface
2. **Monitor Progress:** Watch the real-time progress of the 4-agent workflow
3. **View Results:** Access detailed analysis, comparisons, and recommendations
4. **Export Results:** Download reports in various formats

## 🔍 API Endpoints

- `POST /api/research` - Submit a new research query
- `GET /api/research/{id}` - Get research results
- `GET /api/research` - List all research projects
- `DELETE /api/research/{id}` - Delete a research project

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions, please open an issue in the GitHub repository.
 