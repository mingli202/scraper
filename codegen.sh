#!/bin/bash
set -e

CODEGEN_DIR="../next-schedule-maker/"

cleanup() {
	if [ -f /tmp/api-server.pid ]; then
		kill "$(cat /tmp/api-server.pid)" 2>/dev/null || true
		rm -f /tmp/api-server.pid
		echo "Server stopped."
	fi
}
trap cleanup EXIT

echo "Starting API server..."

source ./.venv/bin/activate
fastapi dev src/api/app.py &
echo $! >/tmp/api-server.pid

echo "Waiting for server..."

for _ in $(seq 1 10); do
	if curl -s http://localhost:8000/openapi.json >/dev/null 2>&1; then break; fi
	sleep 1
done

echo "Generating types..."
bunx @hey-api/openapi-ts -i http://localhost:8000/openapi.json -o "$CODEGEN_DIR/src/client"
bunx @hey-api/openapi-ts -i http://localhost:8000/openapi.json -o "$CODEGEN_DIR/src/types" -p zod

echo "Done!"
