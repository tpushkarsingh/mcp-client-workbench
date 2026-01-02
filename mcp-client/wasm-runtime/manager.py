import os
import httpx
import hashlib
from pathlib import Path

class ToolManager:
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    async def get_tool(self, url: str) -> Path:
        """
        Downloads the WASM binary from the URL if not cached.
        Returns the path to the local file.
        """
        filename = url.split("/")[-1]
        if not filename.endswith(".wasm"):
            filename += ".wasm"
            
        local_path = self.cache_dir / filename
        
        # Simple cache check (for now, assume name uniqueness or url hash)
        # In prod, we'd hash the URL or respect ETags.
        if local_path.exists():
            return local_path

        print(f"Downloading tool from {url}...")
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            resp.raise_for_status()
            local_path.write_bytes(resp.content)
            
        print(f"Saved to {local_path}")
        return local_path
