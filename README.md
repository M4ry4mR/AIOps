# Azure DevOps Log Analyzer

A tool that analyzes Azure DevOps build and release logs using AI to identify issues and provide solutions.

## Features

- Parse and analyze Azure DevOps/TFS build logs
- Extract relevant information from URLs
- Provide AI-powered analysis of log files using multiple AI providers:
  - OpenAI (GPT models)
  - Google Gemini
  - OpenRouter (access to various LLMs)
- Model selection in the web interface
- Web interface for easy interaction
- REST API for integration with other tools

## Project Structure

```
.
├── app.py                  # Application entry point
├── requirements.txt        # Python dependencies
├── setup.py                # Package installation script
├── src/                    # Source code
│   ├── agent/              # Core agent functionality
│   │   ├── ai_agent.py     # AI analysis orchestration
│   │   ├── ai_providers.py # AI provider implementations
│   │   ├── azure_client.py # Azure DevOps client
│   │   └── devops_agent.py # Main agent logic
│   ├── api/                # API endpoints
│   │   └── routes.py       # Flask routes
│   ├── config/             # Configuration
│   │   └── settings.py     # App settings
│   ├── test/               # Test files
│   │   ├── test_ai_agent.py        # AI agent tests
│   │   ├── test_azure_client.py    # Azure client tests
│   │   └── test_devops_agent.py    # DevOps agent tests
│   └── utils/              # Utilities
│       └── logger.py       # Logging configuration
```

## Setup

1. Clone the repository
2. Create and activate a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and update with your credentials:
   ```
   cp .env.example .env
   ```

## Usage

### Running the Web Interface

```
python app.py
```

Then open your browser to http://localhost:5000

The web interface allows you to:
- Enter an Azure DevOps build URL
- Ask a specific question about the build
- Select which AI provider and model to use for analysis

### Using the API

Send a POST request to `/api/analyze` with JSON payload:

```json
{
  "url": "https://dev.azure.com/org/project/_build/results?buildId=12345",
  "query": "What caused this build to fail?",
  "provider": "openai",
  "model": "gpt-4o"
}
```

### Available AI Providers

The application supports the following AI providers:

1. **OpenAI** (`provider: "openai"`)
   - Models: "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"
   - Requires: `AI_API_KEY`

2. **Google Gemini** (`provider: "gemini"`)
   - Models: "gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.0-pro"
   - Requires: `GEMINI_API_KEY`

3. **OpenRouter** (`provider: "openrouter"`)
   - Models: Many models including "openai/gpt-4-turbo", "anthropic/claude-3-opus", "meta-llama/llama-3-70b-instruct"
   - Requires: `OPENROUTER_API_KEY`

## API Endpoints

- `POST /api/analyze`: Analyze build logs
- `GET /api/providers`: Get available AI providers and models

## Testing

Run all tests:

```
python -m unittest discover src/test
```

Run specific test file:

```
python -m unittest src/test/test_azure_client.py
```

## Environment Variables

- `AZURE_DEVOPS_PAT`: Azure DevOps Personal Access Token
- `AZURE_DEVOPS_ORG`: Azure DevOps Organization name
- `AI_API_KEY`: OpenAI API key
- `AI_API_BASE_URL`: Base URL for OpenAI API
- `AI_MODEL`: Default OpenAI model to use

- `GEMINI_API_KEY`: Google Gemini API key
- `GEMINI_MODEL`: Default Gemini model to use

- `OPENROUTER_API_KEY`: OpenRouter API key
- `OPENROUTER_BASE_URL`: Base URL for OpenRouter API

- `DEFAULT_AI_PROVIDER`: Default AI provider to use (openai, gemini, or openrouter)

## License

MIT 