from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse
import numpy as np
import torch
import easyocr
import os
import time
from pdf2image import convert_from_bytes
from dotenv import load_dotenv
from together import Together

router = APIRouter()

# === Load environment ===
load_dotenv()
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
TOGETHER_MODEL = os.getenv(
    "TOGETHER_MODEL", "deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free"
)
client = Together(api_key=TOGETHER_API_KEY)

# === OCR Setup ===
USE_GPU = torch.cuda.is_available()
reader = easyocr.Reader(["en"], gpu=USE_GPU, verbose=False)
print(f"✅ EasyOCR initialized (GPU: {USE_GPU})")

# === Prompt Template ===
PROMPT_TEMPLATE = """
I am uploading a PDF that contains lecture slides. Your task is to generate ultra-detailed, structured notes that completely eliminate the need to refer back to the PDF. Here are the exact requirements:

GOAL:
Produce comprehensive, slide-by-slide notes that capture 100 percent of the relevant information — all text, formulas, diagrams (as descriptive text), lists, and explanations — with zero noise or redundancy.

FORMAT AND STRUCTURE:

1. Section Titles:
   - Use the slide titles or headings as section headers.

2. Content Extraction:
   - Include every point, phrase, formula, table, diagram (summarized), and list.
   - Do not skip over anything useful — even seemingly obvious points.
   - Do not simply copy bullet points — expand them into full explanations where necessary to add clarity and depth.

3. Formatting:
   - Use plain heading levels where needed.
   - Use bulleted and numbered lists for subpoints and sequences.
   - Use plaintext LaTeX syntax for mathematical formulas.
   - Describe diagrams and images in full, detailed text.
   - Format code snippets or pseudocode as code blocks where applicable.

4. No Noise Policy:
   - Remove non-content elements: footers, slide numbers, author bios, logos, repeated navigation text, or any irrelevant metadata.

5. Enrichment (if content is ambiguous or shorthand):
   - Expand acronyms.
   - Reconstruct fragmented or shorthand bullet points into full, clear explanations.
   - Add missing logical connectors or clarifications where necessary.

OPTIONAL (if detected):
   - Add a "Key Takeaways" section at the end of each major topic.
   - Highlight potential exam questions or conceptual pivots.
   - Use "TIP:" or similar markers for important notes or insights.

OUTPUT FORMAT:
   - Plain structured text, or Markdown if formatting clarity helps.
   - Cleanly organized, with clearly separated sections.
   - Fully self-contained notes that make the original PDF unnecessary.

=== BEGIN RAW CONTENT ===
{content}
=== END RAW CONTENT ===
""".strip()


# === Slide Chunking Logic ===
def split_by_slide_count(
    pages: list[str], slides_per_chunk: int = 20
) -> list[list[str]]:
    return [
        pages[i : i + slides_per_chunk] for i in range(0, len(pages), slides_per_chunk)
    ]


# === LLM Streaming (no token limit enforcement) ===
def call_llm_stream(prompt: str):
    try:
        response = client.chat.completions.create(
            model=TOGETHER_MODEL,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            # No explicit max_tokens set
        )
        for chunk in response:
            if hasattr(chunk, "choices") and chunk.choices:
                token = chunk.choices[0].delta.content or ""
                print(token, end="", flush=True)  # Real-time logging
                yield token
    except Exception as e:
        error_msg = f"[LLM ERROR] {e}"
        print(error_msg, flush=True)
        yield f"\n{error_msg}\n"


# === Main FastAPI Endpoint ===
@router.post("/autonotes", response_class=StreamingResponse)
async def auto_generate_notes(file: UploadFile = File(...)):
    try:
        print(f"\n📥 File received: {file.filename}")
        contents = await file.read()

        start_time = time.time()
        images = convert_from_bytes(contents, dpi=96)
        print(
            f"🖼️ Converted {len(images)} page(s) in {round(time.time() - start_time, 2)}s"
        )

        ocr_pages = []
        for idx, image in enumerate(images):
            print(f"🔎 OCR on page {idx + 1}")
            try:
                ocr_result = reader.readtext(np.array(image))
                page_text = "\n".join([line[1] for line in ocr_result])
                ocr_pages.append(page_text)
                print(f"✅ OCR complete for page {idx + 1} ({len(ocr_result)} lines)")
            except Exception as e:
                print(f"❌ OCR failed on page {idx + 1}: {e}")
                ocr_pages.append("")

        chunks = split_by_slide_count(ocr_pages, slides_per_chunk=20)
        print(f"📦 Split into {len(chunks)} chunk(s) of 20 slides each")

        def stream_output():
            for i, chunk in enumerate(chunks):
                chunk_text = "\n\n".join(chunk)
                prompt = PROMPT_TEMPLATE.format(content=chunk_text)

                chunk_header = f"\n\n=== Chunk {i + 1} ===\n"
                print(chunk_header.strip())
                yield chunk_header

                for token in call_llm_stream(prompt):
                    yield token

                chunk_footer = f"\n\n[✓] Done with chunk {i + 1}\n"
                print(chunk_footer.strip())
                yield chunk_footer

        return StreamingResponse(stream_output(), media_type="text/plain")

    except Exception as e:
        print(f"❌ Processing failed: {e}")
        return {"error": str(e)}
