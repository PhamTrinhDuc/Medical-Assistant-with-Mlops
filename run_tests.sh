#!/bin/bash
# Quick start script for running tests

echo "======================================"
echo "Hospital Chatbot - Test Suite Setup"
echo "======================================"
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Install dependencies
echo ""
echo "Installing test dependencies..."
pip install -q -r tests/requirements.txt

# Run tests
echo ""
echo "Running tests..."
echo ""

# Run with different options based on arguments
if [ "$1" == "coverage" ]; then
    pytest --cov=backend --cov-report=html --cov-report=term-missing
    echo ""
    echo "Coverage report generated: htmlcov/index.html"
elif [ "$1" == "watch" ]; then
    pip install -q pytest-watch
    ptw tests/
elif [ "$1" == "quick" ]; then
    pytest -x -v tests/test_health.py tests/test_auth.py
else
    pytest -v
fi

echo ""
echo "Done!"
