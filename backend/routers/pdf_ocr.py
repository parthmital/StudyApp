# backend/routers/pdf_ocr.py

from fastapi import APIRouter, File, UploadFile
from pdf2image import convert_from_bytes
import numpy as np
import torch
import easyocr
import time
import re

router = APIRouter()

# === GPU Setup ===
USE_GPU = torch.cuda.is_available()
print(f"✅ EasyOCR using GPU: {USE_GPU}")
reader = easyocr.Reader(["en"], gpu=USE_GPU, verbose=False)


def clean_text(raw: str) -> str:
    """Cleans OCR output to preserve meaning while removing layout junk."""
    text = raw
    text = re.sub(r"\f", "", text)  # Remove form feeds
    text = re.sub(
        r"Page\s*\d+(\s*of\s*\d+)?", "", text, flags=re.I
    )  # Remove page numbers
    text = re.sub(
        r"^[\s_=\-•●◆■◼◾]{2,}$", "", text, flags=re.MULTILINE
    )  # Divider-only lines
    text = re.sub(r"\n{3,}", "\n\n", text)  # Collapse excessive line breaks
    text = re.sub(r"\s{2,}", " ", text)  # Normalize multi-spaces
    return text.strip()


@router.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        print(f"➡️ Received file: {file.filename}")
        contents = await file.read()
        images = convert_from_bytes(contents, dpi=96)
        total_pages = len(images)
        print(f"🖼️ Converted to {total_pages} page(s)")

        results = []
        start_all = time.time()

        for idx, img in enumerate(images):
            img_np = np.array(img)
            print(f"🔍 OCR Page {idx + 1} using {'GPU' if USE_GPU else 'CPU'}")

            start = time.time()
            try:
                ocr_result = reader.readtext(img_np)
                raw_text = "\n".join([line[1] for line in ocr_result])
                cleaned = clean_text(raw_text)

                results.append(
                    {
                        "page": idx + 1,
                        "raw": raw_text,
                        "cleaned": cleaned,
                        "lines": len(ocr_result),
                        "time": round(time.time() - start, 2),
                    }
                )

                print(
                    f"✅ Page {idx + 1}: {len(ocr_result)} lines, {round(time.time() - start, 2)}s"
                )

            except Exception as e:
                print(f"❌ OCR error on page {idx + 1}: {e}")
                results.append(
                    {
                        "page": idx + 1,
                        "raw": "",
                        "cleaned": f"[ERROR] {str(e)}",
                        "lines": 0,
                        "time": -1,
                    }
                )

        total_time = round(time.time() - start_all, 2)
        print(f"✅ OCR completed for {total_pages} pages in {total_time}s.")

        return {
            "pages": [
                {"page": r["page"], "raw": r["raw"], "cleaned": r["cleaned"]}
                for r in results
            ],
            "stats": {
                "total_pages": total_pages,
                "total_time_sec": total_time,
                "per_page": [
                    {"page": r["page"], "lines": r["lines"], "time_sec": r["time"]}
                    for r in results
                ],
            },
        }

    except Exception as e:
        print(f"❌ Fatal OCR failure: {e}")
        return {"error": str(e)}
