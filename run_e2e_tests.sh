#!/bin/bash

# E2E Test Runner Script
# Runs both API and UI tests for Streamlit workflow

set -e

echo "========================================="
echo "AI Branding Chatbot E2E Test Runner"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if API test should run
run_api_test=true
run_ui_test=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --api-only)
            run_ui_test=false
            shift
            ;;
        --ui-only)
            run_api_test=false
            run_ui_test=true
            shift
            ;;
        --all)
            run_api_test=true
            run_ui_test=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--api-only|--ui-only|--all]"
            exit 1
            ;;
    esac
done

# Run API tests
if [ "$run_api_test" = true ]; then
    echo -e "${YELLOW}Running API-based E2E tests...${NC}"
    echo ""
    
    if python tests/e2e/test_streamlit_workflow.py; then
        echo ""
        echo -e "${GREEN}✅ API tests passed!${NC}"
    else
        echo ""
        echo -e "${RED}❌ API tests failed!${NC}"
        exit 1
    fi
fi

# Run UI tests
if [ "$run_ui_test" = true ]; then
    echo ""
    echo -e "${YELLOW}Running UI-based E2E tests...${NC}"
    echo ""
    
    # Check if Streamlit is running
    if ! curl -s http://localhost:8501 > /dev/null; then
        echo -e "${RED}❌ Streamlit is not running on port 8501${NC}"
        echo "Please start Streamlit first: streamlit run src/streamlit/app.py"
        exit 1
    fi
    
    if python tests/e2e/test_streamlit_ui.py; then
        echo ""
        echo -e "${GREEN}✅ UI tests passed!${NC}"
    else
        echo ""
        echo -e "${RED}❌ UI tests failed!${NC}"
        echo "Check test_failure.png for screenshot"
        exit 1
    fi
fi

echo ""
echo "========================================="
echo -e "${GREEN}✅ All tests completed successfully!${NC}"
echo "========================================="
