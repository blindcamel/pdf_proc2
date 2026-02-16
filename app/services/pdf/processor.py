import fitz  # PyMuPDF
import logging
from pathlib import Path
from typing import List
from app.core.config import settings

logger = logging.getLogger(__name__)

class PDFService:
    """
    Handles physical PDF operations: Text extraction, Image rendering, and Splitting.
    """

    @staticmethod
    def extract_text(file_path: Path) -> str:
        """Extracts all text from a PDF for Tier 1 processing."""
        text = ""
        try:
            with fitz.open(str(file_path)) as doc:
                for page in doc:
                    text += page.get_text() + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Failed to extract text from {file_path}: {e}")
            return ""

    @staticmethod
    def render_page_to_image(file_path: Path, page_index: int = 0) -> bytes:
        """
        Renders a specific page to a high-res PNG for Tier 2 Vision.
        Returns bytes for the LLM backend.
        """
        try:
            with fitz.open(str(file_path)) as doc:
                page = doc.load_page(page_index)
                # Zoom 2.0 (300 DPI) ensures the AI can read small font PO numbers
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                return pix.tobytes("png")
        except Exception as e:
            logger.error(f"Failed to render page {page_index} for {file_path}: {e}")
            raise

    @staticmethod
    def split_pdf(source_path: Path, page_ranges: List[List[int]], output_names: List[str]) -> List[Path]:
        """
        Splits a single PDF into multiple files based on page ranges.
        Example ranges: [[0, 1], [2]] -> 2-page invoice and 1-page invoice.
        """
        output_paths = []
        try:
            with fitz.open(str(source_path)) as src:
                for pages, name in zip(page_ranges, output_names):
                    new_doc = fitz.open()
                    for p in pages:
                        new_doc.insert_pdf(src, from_page=p, to_page=p)
                    
                    # Ensure name ends in .pdf
                    if not name.lower().endswith(".pdf"):
                        name += ".pdf"
                        
                    out_path = settings.PROCESSED_DIR / name
                    new_doc.save(str(out_path))
                    new_doc.close()
                    output_paths.append(out_path)
                    logger.info(f"Created split: {out_path}")
            return output_paths
        except Exception as e:
            logger.error(f"Failed to split PDF {source_path}: {e}")
            raise