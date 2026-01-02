#!/bin/bash
# publish.sh

set -e # Exit immediately if a command exits with a non-zero status

for dir in */ ; do
    # Check if it is a directory and has package.json
    if [ -d "$dir" ] && [ -f "$dir/package.json" ]; then
        echo "Processing $dir..."
        pushd "$dir" > /dev/null
        
        echo "Installing dependencies..."
        npm install
        
        mkdir -p dist
        
        echo "Building..."
        npm run build
        
        # Find the .wasm file in dist/
        if [ ! -d "dist" ]; then
            echo "Error: dist directory not found in $dir"
            popd > /dev/null
            continue
        fi
        
        # Find the first wasm file
        WASM_FILE=$(find dist -maxdepth 1 -name "*.wasm" | head -n 1)
        
        if [ -z "$WASM_FILE" ]; then
            echo "Error: No .wasm file found in $dir/dist"
            popd > /dev/null
            continue
        fi
        
        BINARY_NAME=$(basename "$WASM_FILE")
        
        echo "Uploading $BINARY_NAME to Artifactory..."
        curl -f -X POST "http://localhost:8001/upload" \
             -F "file=@$WASM_FILE"
             
        echo ""
        
        # Register with MCP Registry
        # Extract version and description using node for convenience (since we have npm)
        VERSION=$(node -p "require('./package.json').version")
        NAME=$(node -p "require('./package.json').name")
        DESC=$(node -p "require('./package.json').description || ''")
        
        echo "Registering $NAME@$VERSION with Registry..."
        
        # Construct JSON payload
        # Note: escaping quotes carefully
        cat <<EOF > /tmp/register_payload.json
{
  "name": "$NAME",
  "version": "$VERSION",
  "description": "$DESC",
  "binaryUrl": "http://localhost:8001/binaries/$BINARY_NAME",
  "runtimeConfig": {}
}
EOF

        curl -X POST "http://localhost:8002/api/v1/servers" \
             -H "Content-Type: application/json" \
             -d @/tmp/register_payload.json
             
        echo "" # New line for readability
        popd > /dev/null
        echo "-----------------------------------"
    fi
done