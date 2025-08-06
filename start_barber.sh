#!/bin/bash

# Start the Ez_Biz Barber Instance
# This script starts the barber shop application on port 8505

echo "Starting Ez_Biz Barber Shop Application..."
echo "Application will be available at: http://localhost:8505"
echo "Press Ctrl+C to stop the application"
echo ""

# Navigate to the barber directory
cd "$(dirname "$0")"

# Start streamlit on port 8505 to avoid conflicts with carpet instance
streamlit run main.py --server.port 8505