from fastapi import APIRouter, File, UploadFile
from pdf2image import convert_from_bytes
from paddleocr import PaddleOCR
import tempfile
import os

router = APIRouter()
ocr = PaddleOCR(use_angle_cls=True, lang="en")


@router.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    with tempfile.TemporaryDirectory() as tmpdir:
        contents = await file.read()
        images = convert_from_bytes(contents)

        text_output = []
        for idx, img in enumerate(images):
            img_path = os.path.join(tmpdir, f"page_{idx}.jpg")
            img.save(img_path)
            result = ocr.ocr(img_path, cls=True)
            text = "\n".join([line[1][0] for line in result[0]])
            text_output.append(text)

    return {"pages": text_output}