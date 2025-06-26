# backend/routers/pdf_ocr.py

from fastapi import APIRouter, File, UploadFile
from pdf2image import convert_from_bytes
import concurrent.futures
import numpy as np
import torch
import easyocr
import time

router = APIRouter()

# ✅ Initialize a reader just to log GPU status
gpu_available = torch.cuda.is_available()
print(f"✅ EasyOCR using GPU: {gpu_available}")


# ✅ This runs in each subprocess (must be top-level for pickling)
def ocr_worker(image_array, page_idx):
    """Per-process OCR worker with its own EasyOCR instance."""
    reader = easyocr.Reader(["en"], gpu=torch.cuda.is_available(), verbose=False)
    start = time.time()
    try:
        result = reader.readtext(image_array)
        text = "\n".join([line[1] for line in result])
        duration = round(time.time() - start, 2)
        return {
            "page": page_idx + 1,
            "text": text,
            "lines": len(result),
            "time": duration,
        }
    except Exception as e:
        return {
            "page": page_idx + 1,
            "text": f"[ERROR] {str(e)}",
            "lines": 0,
            "time": -1,
        }


# ✅ Wrapper to avoid lambda (safe for multiprocessing on Windows)
def unwrap_args_ocr_worker(args):
    return ocr_worker(*args)


@router.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        print(f"➡️ Received file: {file.filename}")
        contents = await file.read()
        print(f"📦 PDF Size: {len(contents)} bytes")

        # ✅ Convert to images at reduced DPI for speed
        start_all = time.time()
        images = convert_from_bytes(contents, dpi=96)
        print(f"🖼️ Converted into {len(images)} page(s)")

        # ✅ Prepare image arrays for multiprocessing
        image_data = [(np.array(img), idx) for idx, img in enumerate(images)]

        # ✅ Use all CPU cores for OCR
        with concurrent.futures.ProcessPoolExecutor() as executor:
            results = list(executor.map(unwrap_args_ocr_worker, image_data))

        total_time = round(time.time() - start_all, 2)
        print(f"✅ OCR completed in {total_time}s.")

        return {
            "pages": [r["text"] for r in results],
            "stats": {
                "total_pages": len(results),
                "total_time_sec": total_time,
                "per_page": [
                    {"page": r["page"], "lines": r["lines"], "time_sec": r["time"]}
                    for r in results
                ],
            },
        }

    except Exception as e:
        print(f"❌ Fatal error: {e}")
        return {"error": str(e)}