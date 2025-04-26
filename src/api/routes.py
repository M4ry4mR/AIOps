from flask import Flask, request, jsonify, render_template_string, Response, stream_with_context
import time
import json
import logging
import threading
import queue
from src.agent import DevOpsAgent
from src.config.settings import AI_PROVIDERS, DEFAULT_AI_PROVIDER
from src.agent.ai_providers import get_ai_provider

# Initialize agent
devops_agent = DevOpsAgent()

# Create Flask app
app = Flask(__name__)

# Create a queue for progress updates
progress_updates = {}

# Add a simple debug endpoint
@app.route('/debug', methods=['GET'])
def debug():
    """Simple debug endpoint to test API connectivity."""
    return jsonify({
        "status": "ok",
        "message": "API is working",
        "providers": AI_PROVIDERS,
        "default_provider": DEFAULT_AI_PROVIDER
    })

# Add a provider test endpoint
@app.route('/test_provider/<provider_name>', methods=['GET'])
def test_provider(provider_name):
    """Test a specific AI provider."""
    try:
        model = request.args.get('model', None)
        provider = get_ai_provider(provider_name, model)
        
        # Just initialize the provider without making an actual API call
        return jsonify({
            "status": "ok",
            "message": f"Successfully initialized {provider_name} provider",
            "model": model or "default model",
            "provider_type": provider.__class__.__name__
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# SSE endpoint for progress updates
@app.route('/stream-progress/<session_id>', methods=['GET'])
def stream_progress(session_id):
    """Stream progress updates to the client."""
    def generate():
        if session_id not in progress_updates:
            progress_updates[session_id] = queue.Queue()
        
        q = progress_updates[session_id]
        
        # Send initial event
        yield 'data: ' + json.dumps({"status": "initializing", "message": "Starting analysis..."}) + '\n\n'
        
        while True:
            try:
                # Get updates from the queue with a timeout
                update = q.get(timeout=1)
                if update == "DONE":
                    yield 'data: ' + json.dumps({"status": "complete", "message": "Analysis complete"}) + '\n\n'
                    break
                yield 'data: ' + json.dumps(update) + '\n\n'
            except queue.Empty:
                # Send heartbeat to keep connection alive
                yield ': heartbeat\n\n'
            except Exception as e:
                yield 'data: ' + json.dumps({"status": "error", "message": str(e)}) + '\n\n'
                break
    
    return Response(stream_with_context(generate()), content_type='text/event-stream')

# Background task for processing requests
def process_in_background(text, user_id, provider, model, session_id):
    """Process a request in the background and update progress."""
    q = progress_updates[session_id]
    
    # Update progress based on logs
    def log_handler(record):
        msg = record.getMessage()
        if "Initializing" in msg:
            q.put({"status": "initializing", "message": msg})
        elif "Parsing" in msg:
            q.put({"status": "parsing", "message": "Parsing Azure DevOps URL..."})
        elif "Retrieving logs" in msg:
            q.put({"status": "retrieving", "message": "Retrieving build logs..."})
        elif "Successfully retrieved logs" in msg:
            q.put({"status": "processing", "message": "Processing log data..."})
        elif "Starting log analysis" in msg:
            q.put({"status": "analyzing", "message": f"Analyzing with {provider}..."})
        elif "Sending request to" in msg:
            q.put({"status": "generating", "message": "Generating analysis..."})
        elif "Successfully generated" in msg or "Analysis complete" in msg:
            q.put({"status": "finishing", "message": "Completing analysis..."})
        # Add more detailed status updates based on more log messages
        elif "Error retrieving" in msg:
            q.put({"status": "error", "message": "Error retrieving logs: " + msg})
        elif "Failed to parse" in msg:
            q.put({"status": "error", "message": "Failed to parse URL: " + msg})
        elif "error" in msg.lower() or "exception" in msg.lower():
            q.put({"status": "error", "message": "Error: " + msg})
    
    # Add handler to capture log messages
    handler = logging.Handler()
    handler.emit = log_handler
    logger = logging.getLogger()
    logger.addHandler(handler)
    
    try:
        # Process request
        devops_agent.process_request(text, user_id, provider, model)
    finally:
        # Remove handler
        logger.removeHandler(handler)
        # Signal completion
        q.put("DONE")

# Models available for each provider
PROVIDER_MODELS = {
    "openai": [
        "gpt-4o",
        "gpt-4-turbo",
        "gpt-3.5-turbo"
    ],
    "openrouter": [
        "openai/gpt-4-turbo",
        "anthropic/claude-3-opus",
        "anthropic/claude-3-sonnet",
        "mistralai/mistral-large",
        "meta-llama/llama-3-70b-instruct"
    ],
    "gemini": [
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-1.0-pro"
    ]
}

# Basic HTML template for the web interface
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Azure DevOps Log Analyzer</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input[type="text"], textarea, select {
            width: 100%;
            padding: 8px;
            box-sizing: border-box;
        }
        textarea {
            height: 120px;
        }
        button {
            background-color: #0078d4;
            color: white;
            border: none;
            padding: 10px 15px;
            cursor: pointer;
            margin-right: 10px;
        }
        .secondary-button {
            background-color: #666;
        }
        .url-valid {
            color: green;
            font-weight: bold;
            display: none;
            margin-top: 5px;
        }
        .url-invalid {
            color: red;
            font-weight: bold;
            display: none;
            margin-top: 5px;
        }
        .results {
            margin-top: 20px;
            white-space: pre-wrap;
            border: 1px solid #ddd;
            padding: 15px;
            background-color: #f8f8f8;
        }
        .model-selector {
            display: flex;
            gap: 10px;
        }
        .model-selector > div {
            flex: 1;
        }
        .loader {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #0078d4;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            display: inline-block;
            margin-right: 10px;
            vertical-align: middle;
        }
        .loading-info {
            display: none;
            margin-top: 20px;
            padding: 15px;
            background-color: #f0f7ff;
            border: 1px solid #cce5ff;
            border-radius: 4px;
        }
        .state {
            font-weight: bold;
            color: #0078d4;
        }
        .error-state {
            font-weight: bold;
            color: #d40000;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .progress-bar {
            height: 6px;
            background-color: #ddd;
            border-radius: 3px;
            margin-top: 10px;
            overflow: hidden;
        }
        .progress-value {
            height: 100%;
            background-color: #0078d4;
            width: 10%;
            border-radius: 3px;
            transition: width 0.5s;
        }
        .status-history {
            margin-top: 10px;
            max-height: 100px;
            overflow-y: auto;
            font-size: 12px;
            color: #666;
        }
    </style>
    <script>
        // Generate a unique session ID
        const sessionId = Date.now().toString() + Math.random().toString(36).substr(2, 5);
        let eventSource;
        let progressSteps = [
            "Initializing", 
            "Connecting to Azure DevOps",
            "Parsing URLs",
            "Retrieving build info",
            "Fetching build logs",
            "Processing log data",
            "Initializing AI model",
            "Analyzing build failures",
            "Generating recommendations",
            "Preparing results"
        ];
        let currentProgressStep = 0;
        let statusHistory = [];
        
        function updateModelOptions() {
            const provider = document.getElementById('provider').value;
            const modelSelect = document.getElementById('model');
            
            // Clear existing options
            modelSelect.innerHTML = '';
            
            // Get models for the selected provider
            const models = {
                'openai': ['gpt-4o', 'gpt-4-turbo', 'gpt-3.5-turbo'],
                'openrouter': ['openai/gpt-4-turbo', 'anthropic/claude-3-opus', 'anthropic/claude-3-sonnet', 'mistralai/mistral-large', 'meta-llama/llama-3-70b-instruct'],
                'gemini': ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-1.0-pro']
            };
            
            // Add options for the selected provider
            if (provider in models) {
                models[provider].forEach(model => {
                    const option = document.createElement('option');
                    option.value = model;
                    option.textContent = model;
                    modelSelect.appendChild(option);
                });
            }
        }
        
        function validateURL(url) {
            // Basic validation for Azure DevOps URL
            return url && 
                   url.trim() !== '' && 
                   (url.includes('buildId=') || url.includes('_build/')) && 
                   (url.includes('tfs/') || url.includes('azure'));
        }
        
        function testURL() {
            const urlInput = document.getElementById('url');
            const url = urlInput.value.trim();
            const validElement = document.getElementById('url-valid');
            const invalidElement = document.getElementById('url-invalid');
            
            if (validateURL(url)) {
                validElement.style.display = 'block';
                invalidElement.style.display = 'none';
            } else {
                validElement.style.display = 'none';
                invalidElement.style.display = 'block';
            }
        }
        
        function showLoading() {
            // Validate URL before submission
            const urlInput = document.getElementById('url');
            const url = urlInput.value.trim();
            
            if (!validateURL(url)) {
                alert('Please enter a valid Azure DevOps URL with a buildId parameter');
                return false;
            }
            
            document.getElementById('loading-info').style.display = 'block';
            document.getElementById('analyzeBtn').disabled = true;
            document.getElementById('url').disabled = true;
            document.getElementById('query').disabled = true;
            document.getElementById('provider').disabled = true;
            document.getElementById('model').disabled = true;
            document.getElementById('testUrlBtn').disabled = true;
            
            // Initialize status history
            statusHistory = [];
            document.getElementById('status-history').innerHTML = '';
            
            // Start progress updates
            startProgressUpdates();
            
            return true;
        }
        
        function addStatusMessage(message, isError = false) {
            const historyDiv = document.getElementById('status-history');
            const timestamp = new Date().toLocaleTimeString();
            
            // Add to our array
            statusHistory.push({message, timestamp, isError});
            
            // Keep only last 20 messages
            if (statusHistory.length > 20) {
                statusHistory.shift();
            }
            
            // Update display
            historyDiv.innerHTML = '';
            statusHistory.forEach(status => {
                const msgClass = status.isError ? 'error-state' : '';
                historyDiv.innerHTML += `<div class="${msgClass}">[${status.timestamp}] ${status.message}</div>`;
            });
            
            // Scroll to bottom
            historyDiv.scrollTop = historyDiv.scrollHeight;
        }
        
        function startProgressUpdates() {
            // Connect to the server-sent events endpoint
            eventSource = new EventSource(`/stream-progress/${sessionId}`);
            
            // Progress bar 
            let progressBar = document.querySelector('.progress-value');
            let progressPercent = 10;
            
            // Handle incoming events
            eventSource.onmessage = function(event) {
                const data = JSON.parse(event.data);
                
                if (data.status === "complete") {
                    // Analysis complete, progress to 100%
                    progressPercent = 100;
                    progressBar.style.width = progressPercent + '%';
                    addStatusMessage("Analysis complete");
                    
                    // Disconnect from the stream
                    if (eventSource) {
                        eventSource.close();
                    }
                    
                    // We'll let the page reload handle this
                    return;
                }
                
                // Update the state message
                const stateElement = document.getElementById('current-state');
                if (stateElement) {
                    const message = data.message || progressSteps[currentProgressStep];
                    stateElement.textContent = message;
                    
                    // Add message to history
                    const isError = data.status === "error";
                    if (isError) {
                        stateElement.className = 'error-state';
                    } else {
                        stateElement.className = 'state';
                    }
                    
                    addStatusMessage(message, isError);
                    
                    // Update progress bar (only for non-error statuses)
                    if (!isError) {
                        currentProgressStep++;
                        progressPercent = Math.min(90, 10 + (currentProgressStep * 8));
                        progressBar.style.width = progressPercent + '%';
                    } else {
                        // For errors, set progress bar to red
                        progressBar.style.backgroundColor = '#d40000';
                    }
                }
            };
            
            eventSource.onerror = function(event) {
                console.error("EventSource error:", event);
                addStatusMessage("Connection error with server", true);
                if (eventSource) {
                    eventSource.close();
                }
            };
        }
        
        document.addEventListener('DOMContentLoaded', function() {
            updateModelOptions();
            document.getElementById('provider').addEventListener('change', updateModelOptions);
            
            // Add session ID to the form
            const form = document.getElementById('analyzeForm');
            const sessionInput = document.createElement('input');
            sessionInput.type = 'hidden';
            sessionInput.name = 'session_id';
            sessionInput.value = sessionId;
            form.appendChild(sessionInput);
            
            // Handle form submission
            form.addEventListener('submit', function(e) {
                // Check if URL is provided and valid
                const urlInput = document.getElementById('url');
                const url = urlInput.value.trim();
                
                if (!validateURL(url)) {
                    e.preventDefault();
                    alert('Please enter a valid Azure DevOps URL with a buildId parameter');
                    return false;
                }
                
                return showLoading();
            });
            
            // Add URL validation on input change
            document.getElementById('url').addEventListener('input', function() {
                // Hide status indicators when typing
                document.getElementById('url-valid').style.display = 'none';
                document.getElementById('url-invalid').style.display = 'none';
            });
        });
    </script>
</head>
<body>
    <h1>Azure DevOps Log Analyzer</h1>
    <form id="analyzeForm" method="POST" action="/">
        <div class="form-group">
            <label for="url">Azure DevOps Build URL:</label>
            <input type="text" id="url" name="url" required 
                   placeholder="Enter Azure DevOps URL here (e.g., https://azure.asax.ir/tfs/...)"
                   value="" 
                   pattern=".*buildId=\d+.*"
                   title="URL must contain a buildId parameter">
            <small style="display: block; margin-top: 5px; color: #666;">
                Example: https://azure.asax.ir/tfs/AsaProjects/Financial/_build/results?buildId=871225
            </small>
            <div id="url-valid" class="url-valid">✓ URL looks valid</div>
            <div id="url-invalid" class="url-invalid">✗ URL doesn't seem to be a valid Azure DevOps URL</div>
            <button type="button" id="testUrlBtn" class="secondary-button" onclick="testURL()">Test URL</button>
        </div>
        <div class="form-group">
            <label for="query">Question (optional):</label>
            <textarea id="query" name="query" placeholder="What went wrong in this build?"></textarea>
        </div>
        <div class="form-group">
            <label>AI Model:</label>
            <div class="model-selector">
                <div>
                    <label for="provider">Provider:</label>
                    <select id="provider" name="provider">
                        {% for provider_id, provider_name in providers.items() %}
                            <option value="{{ provider_id }}" {% if provider_id == default_provider %}selected{% endif %}>{{ provider_name }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div>
                    <label for="model">Model:</label>
                    <select id="model" name="model">
                        <!-- Options filled by JavaScript -->
                    </select>
                </div>
            </div>
        </div>
        <button type="submit" id="analyzeBtn">Analyze Logs</button>
    </form>
    
    <div id="loading-info" class="loading-info">
        <div class="loader"></div>
        <span>Analyzing logs... <span id="current-state" class="state">Initializing...</span></span>
        <div class="progress-bar">
            <div class="progress-value"></div>
        </div>
        <div id="status-history" class="status-history"></div>
    </div>
    
    {% if result %}
    <div class="results">
        <h2>Analysis:</h2>
        <p><strong>Using {{ used_provider }} / {{ used_model }}</strong></p>
        {{ result|safe }}
    </div>
    <script>
        // Hide loading indicator and re-enable form when results are shown
        document.getElementById('loading-info').style.display = 'none';
        document.getElementById('analyzeBtn').disabled = false;
        document.getElementById('url').disabled = false;
        document.getElementById('query').disabled = false;
        document.getElementById('provider').disabled = false;
        document.getElementById('model').disabled = false;
        
        // Clean up event source
        if (eventSource) {
            eventSource.close();
        }
    </script>
    {% endif %}
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    """Main route for the web interface."""
    result = None
    used_provider = DEFAULT_AI_PROVIDER
    used_model = None
    
    if request.method == 'POST':
        # Add debug logging to see raw form input
        logger = logging.getLogger(__name__)
        logger.info(f"Raw form data received: {request.form}")
        
        url = request.form.get('url', '').strip()
        logger.info(f"Original URL from form: '{url}'")
        
        # Remove leading @ if present
        if url.startswith('@'):
            url = url[1:]
            logger.info(f"URL after @ removal: '{url}'")
        
        query = request.form.get('query', 'What caused this build to fail and how can I fix it?')
        provider = request.form.get('provider', DEFAULT_AI_PROVIDER)
        model = request.form.get('model')
        session_id = request.form.get('session_id', '')
        
        used_provider = provider
        used_model = model
        
        # Add session to progress updates if not already there
        if session_id and session_id not in progress_updates:
            progress_updates[session_id] = queue.Queue()
        
        # Make sure URL is properly formatted
        if url and not (url.startswith('http://') or url.startswith('https://')):
            url = 'https://' + url
            logger.info(f"URL after adding https://: '{url}'")
            
        # Combine URL and query to match expected format
        text = f"{url} {query}"
        logger.info(f"Final text sent to process_request: '{text}'")
        
        if session_id:
            # Start processing in background
            threading.Thread(
                target=process_in_background,
                args=(text, "web_user", provider, model, session_id)
            ).start()
        
        # Process request with selected model
        result = devops_agent.process_request(
            text, 
            user_id="web_user", 
            provider=provider, 
            model=model
        )
    
    return render_template_string(
        HTML_TEMPLATE, 
        result=result, 
        providers=AI_PROVIDERS,
        default_provider=DEFAULT_AI_PROVIDER,
        used_provider=used_provider,
        used_model=used_model
    )

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """API endpoint for analyzing Azure DevOps logs."""
    data = request.json
    
    if not data or 'url' not in data:
        return jsonify({"error": "URL is required"}), 400
    
    url = data.get('url', '').strip()
    # Remove leading @ if present
    if url.startswith('@'):
        url = url[1:]
        
    # Make sure URL is properly formatted
    if url and not (url.startswith('http://') or url.startswith('https://')):
        url = 'https://' + url
    
    query = data.get('query', 'What caused this build to fail and how can I fix it?')
    user_id = data.get('user_id', 'api_user')
    provider = data.get('provider', DEFAULT_AI_PROVIDER)
    model = data.get('model')
    
    # Combine URL and query
    text = f"{url} {query}"
    
    # Process request with the specified provider and model
    result = devops_agent.process_request(
        text, 
        user_id=user_id,
        provider=provider,
        model=model
    )
    
    return jsonify({
        "result": result,
        "provider": provider,
        "model": model
    })

@app.route('/api/providers', methods=['GET'])
def get_providers():
    """API endpoint to get available AI providers and models."""
    return jsonify({
        "providers": AI_PROVIDERS,
        "models": PROVIDER_MODELS,
        "default_provider": DEFAULT_AI_PROVIDER
    }) 