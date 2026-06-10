from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import shutil
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse


from pipeline import run_pipeline

#uvicorn app:app --reload
app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def home():
    with open("templates/index.html", "r") as f:
        return f.read()

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):

    pdf_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(pdf_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Run your pipeline
    output_json = run_pipeline(pdf_path)

    return FileResponse(
        output_json,
        media_type="application/json",
        filename="toc_parsed.json"
    )