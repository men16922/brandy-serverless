#!/bin/bash
# Script to run Streamlit app for development

set -e

echo "🚀 Starting Streamlit App..."

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Virtual environment not detected. Activating..."
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        echo "✅ Virtual environment activated"
    else
        echo "❌ Virtual environment not found. Please run: python3 -m venv venv && source venv/bin/activate"
        exit 1
    fi
fi

# Check if dependencies are installed
echo "📦 Checking dependencies..."
if ! python -c "import streamlit" 2>/dev/null; then
    echo "📦 Installing Streamlit dependencies..."
    pip install -r src/streamlit/requirements.txt
fi

# Set environment variables
export API_BASE_URL=${API_BASE_URL:-"http://localhost:3000"}
export STREAMLIT_SERVER_PORT=${STREAMLIT_SERVER_PORT:-8501}

echo "🌐 API Base URL: $API_BASE_URL"
echo "🌐 Streamlit Port: $STREAMLIT_SERVER_PORT"

# Check if SAM Local API is running
echo "🔍 Checking SAM Local API..."
if curl -s "$API_BASE_URL/health" >/dev/null 2>&1; then
    echo "✅ SAM Local API is running"
else
    echo "⚠️  SAM Local API not detected at $API_BASE_URL"
    echo "💡 Start it with: sam local start-api --port 3000"
    echo "   Or set API_BASE_URL to your deployed API endpoint"
fi

# Run Streamlit app
echo "🎨 Starting Streamlit app..."
echo "📱 Open your browser to: http://localhost:$STREAMLIT_SERVER_PORT"

cd src/streamlit
streamlit run app.py --server.port $STREAMLIT_SERVER_PORT --server.address 0.0.0.0