import argparse
import os
import tempfile
import time
from typing import List, Optional
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from markitdown import MarkItDown

app = FastAPI(
    title="MarkItDown Web GUI",
    description="Interactive Web GUI and REST API for converting documents to Markdown.",
    version="0.1.0",
)

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

md_engine = MarkItDown()

SUPPORTED_EXTENSIONS = [
    ".pdf", ".docx", ".pptx", ".xlsx", ".xls", ".html", ".htm",
    ".epub", ".msg", ".zip", ".csv", ".json", ".xml", ".txt",
    ".png", ".jpg", ".jpeg", ".wav", ".mp3", ".m4a"
]


@app.get("/", response_class=HTMLResponse)
async def get_index():
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Index page not found")
    return HTMLResponse(content=index_path.read_text(encoding="utf-8"))


@app.get("/api/supported-formats")
async def get_supported_formats():
    return {
        "formats": SUPPORTED_EXTENSIONS,
        "converters": [
            "PdfConverter", "DocxConverter", "PptxConverter", "XlsxConverter",
            "HtmlConverter", "EpubConverter", "OutlookMsgConverter", "ZipConverter",
            "CsvConverter", "ImageConverter", "AudioConverter", "PlainTextConverter"
        ]
    }


@app.post("/api/convert")
async def convert_file(
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    enable_plugins: bool = Form(False),
):
    if not file and not url:
        raise HTTPException(status_code=400, detail="Must provide either a file or a URL")

    start_time = time.perf_counter()
    engine = md_engine if not enable_plugins else MarkItDown(enable_plugins=True)

    if url:
        try:
            res = engine.convert(url)
            duration = time.perf_counter() - start_time
            return {
                "filename": url,
                "title": res.title or url,
                "markdown": res.markdown,
                "duration_seconds": round(duration, 3),
                "char_count": len(res.markdown),
                "word_count": len(res.markdown.split()),
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Conversion error: {str(e)}")

    if file:
        filename = file.filename or "uploaded_file"
        suffix = Path(filename).suffix
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            res = engine.convert(tmp_path)
            duration = time.perf_counter() - start_time
            return {
                "filename": filename,
                "title": res.title or filename,
                "markdown": res.markdown,
                "duration_seconds": round(duration, 3),
                "char_count": len(res.markdown),
                "word_count": len(res.markdown.split()),
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Conversion failed for {filename}: {str(e)}")
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


@app.post("/api/convert-batch")
async def convert_batch_files(
    files: List[UploadFile] = File(...),
    enable_plugins: bool = Form(False),
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    start_time = time.perf_counter()
    engine = md_engine if not enable_plugins else MarkItDown(enable_plugins=True)

    temp_paths = []
    filenames = []
    for file in files:
        filename = file.filename or "uploaded_file"
        filenames.append(filename)
        suffix = Path(filename).suffix
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            content = await file.read()
            tmp.write(content)
            temp_paths.append(tmp.name)

    try:
        results = engine.convert_batch(temp_paths)
        total_duration = time.perf_counter() - start_time
        
        response_items = []
        for fn, res in zip(filenames, results):
            response_items.append({
                "filename": fn,
                "title": res.title or fn,
                "markdown": res.markdown,
                "char_count": len(res.markdown),
                "word_count": len(res.markdown.split()),
            })

        return {
            "total_files": len(results),
            "total_duration_seconds": round(total_duration, 3),
            "results": response_items,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch conversion error: {str(e)}")
    finally:
        for tp in temp_paths:
            if os.path.exists(tp):
                os.unlink(tp)


def main():
    parser = argparse.ArgumentParser(description="Start the MarkItDown Web GUI server")
    parser.add_argument("--host", default="127.0.0.1", help="Host IP address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port number (default: 8000)")
    args = parser.parse_args()

    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
