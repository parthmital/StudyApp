# backend/routers/pdf_ocr.py

from fastapi import APIRouter, File, UploadFile
from pdf2image import convert_from_bytes
import numpy as np
import torch
import easyocr
import time

router = APIRouter()

# ✅ Detect GPU availability
USE_GPU = torch.cuda.is_available()
print(f"✅ EasyOCR will use GPU: {USE_GPU}")

# ✅ Initialize EasyOCR reader (once)
reader = easyocr.Reader(["en"], gpu=USE_GPU, verbose=False)


@router.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        print(f"➡️ Received file: {file.filename}")
        contents = await file.read()
        print(f"📦 PDF Size: {len(contents)} bytes")

        start_all = time.time()
        images = convert_from_bytes(contents, dpi=96)
        num_pages = len(images)
        print(f"🖼️ Converted to {num_pages} page(s)")

        results = []

        # 🔁 Sequential OCR on all pages
        for idx, img in enumerate(images):
            img_np = np.array(img)
            print(f"🔍 Page {idx + 1} → OCR using {'GPU' if USE_GPU else 'CPU'}")
            start = time.time()
            try:
                result = reader.readtext(img_np)
                results.append(
                    {
                        "page": idx + 1,
                        "text": "\n".join([line[1] for line in result]),
                        "lines": len(result),
                        "time": round(time.time() - start, 2),
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "page": idx + 1,
                        "text": f"[ERROR] {str(e)}",
                        "lines": 0,
                        "time": -1,
                    }
                )

        total_time = round(time.time() - start_all, 2)
        print(f"✅ OCR completed in {total_time}s.")

        return {
            "pages": [r["text"] for r in results],
            "stats": {
                "total_pages": num_pages,
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
