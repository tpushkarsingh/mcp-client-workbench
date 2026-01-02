from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse
import os
import shutil

app = FastAPI(title="Artifactory Binary Upload API", description="API for uploading binary files to Artifactory", version="1.0.0")
STORAGE_DIR = "binaries"
os.makedirs(STORAGE_DIR, exist_ok=True)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/binaries/{filename}")
async def get_wasm(filename: str):
    file_path = os.path.join(STORAGE_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Wasm binary not found")
    return FileResponse(path=file_path, media_type="application/wasm")

@app.post("/upload")
async def upload_wasm(file: UploadFile = File(...)):
    if not file.filename.endswith(".wasm"):
        raise HTTPException(status_code=400, detail="Invalid file type")
    file_path = os.path.join(STORAGE_DIR, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"url": f"http://localhost:8001/binaries/{file.filename}", "status": "success"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)