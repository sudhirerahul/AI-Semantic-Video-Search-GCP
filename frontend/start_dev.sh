#!/bin/bash

# Quick Start Script for Local Development
# Starts both backend API and frontend dev server

set -e

PROJECT_ROOT="/Users/sudhirerahul/Desktop/GCP_Media_proto"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

echo "=========================================="
echo "Starting GCP Media - Full Stack"
echo "=========================================="
echo ""

# Check if backend is already running
if lsof -ti:8080 >/dev/null 2>&1; then
    echo "✅ Backend API already running on port 8080"
    echo ""
else
    echo "Backend API not running. Please start it manually in a separate terminal:"
    echo ""
    echo "  cd $PROJECT_ROOT"
    echo "  ./start_cloud_clip.sh"
    echo ""
    echo "Then press Enter to continue, or Ctrl+C to exit..."
    read -r

    # Verify backend is now running
    if ! curl -s http://localhost:8080/health > /dev/null 2>&1; then
        echo "❌ Backend API still not running"
        echo "Please start it and try again"
        exit 1
    fi
    echo "✅ Backend API detected on port 8080"
    echo ""
fi

# Check if node_modules exists
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd "$FRONTEND_DIR"
    npm install
    echo "✅ Dependencies installed"
    echo ""
fi

# Create .env.local if it doesn't exist
if [ ! -f "$FRONTEND_DIR/.env.local" ]; then
    echo "Creating .env.local..."
    cat > "$FRONTEND_DIR/.env.local" <<'EOF'
NEXT_PUBLIC_API_BASE=http://localhost:8080
EOF
    echo "✅ Environment variables configured"
    echo ""
fi

# Start frontend
echo "Starting Frontend (port 3000)..."
cd "$FRONTEND_DIR"
npm run dev &
FRONTEND_PID=$!

# Wait for frontend to start
echo "Waiting for frontend to initialize (5s)..."
sleep 5

echo ""
echo "=========================================="
echo "✅ All Services Running"
echo "=========================================="
echo ""
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8080"
echo ""
echo "Process IDs:"
echo "  Backend:  $BACKEND_PID"
echo "  Frontend: $FRONTEND_PID"
echo ""
echo "Stop services:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "View logs:"
echo "  Backend:  tail -f /tmp/cloud_clip_api.log"
echo "  Frontend: (output shown in this terminal)"
echo ""

# Keep script running to show frontend logs
wait $FRONTEND_PID
