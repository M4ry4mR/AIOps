import os
import sys
from src.utils.logger import setup_logging
from src.api.routes import app
from dotenv import load_dotenv

print("Starting application...")

# Load environment variables
load_dotenv()
print("Environment variables loaded")

# Setup logging
logger = setup_logging()
print("Logging configured")

if __name__ == "__main__":
    print("Running as main module")
    logger.info("Starting Azure DevOps Log Analyzer")
    
    # Get port from environment or use default (now 7000)
    port = int(os.environ.get("PORT", 7000))
    print(f"Using port {port}")
    
    # Dump environment variables for debugging
    print("Environment variables:")
    for key, value in os.environ.items():
        if key.startswith(("FLASK", "AI_", "OPENAI", "GEMINI", "OPENROUTER")):
            sanitized_value = value[:5] + "..." if "KEY" in key else value
            print(f"  {key}={sanitized_value}")
    
    # Run app
    print(f"Running app on 0.0.0.0:{port} with debug={os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'}")
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG", "False").lower() == "true") 