from typing import List
import os
import logging

logger = logging.getLogger(__name__)


def extract_text_from_pdf(path: str) -> str:
    """Extract text from a PDF file with proper error handling.

    Uses pypdf (maintained fork of PyPDF2) for reliable text extraction.
    Validates file existence and provides clear error messages.

    Args:
        path: Path to the PDF file

    Returns:
        Extracted text from all pages

    Raises:
        FileNotFoundError: If PDF file doesn't exist
        ValueError: If file is not a valid PDF or extraction fails
    """
    # Validate file exists
    if not os.path.exists(path):
        logger.error(f"PDF file not found: {path}")
        raise FileNotFoundError(f"PDF file does not exist: {path}")

    # Validate file is readable
    if not os.path.isfile(path):
        logger.error(f"Path is not a file: {path}")
        raise ValueError(f"Path is not a file: {path}")

    # Validate file extension
    if not path.lower().endswith('.pdf'):
        logger.warning(f"File does not have .pdf extension: {path}")

    try:
        # Try pypdf first (maintained fork)
        try:
            from pypdf import PdfReader
            logger.info(f"Using pypdf for PDF extraction from: {path}")
        except ImportError:
            # Fallback to PyPDF2 if pypdf not available
            from PyPDF2 import PdfReader
            logger.warning("pypdf not found, using deprecated PyPDF2. Please upgrade to pypdf.")

        reader = PdfReader(path)

        # Validate PDF has pages
        if len(reader.pages) == 0:
            logger.warning(f"PDF has no pages: {path}")
            return ""

        # Extract text from all pages
        pages = []
        for i, page in enumerate(reader.pages):
            try:
                txt = page.extract_text()
                if txt and txt.strip():
                    pages.append(txt)
                else:
                    logger.debug(f"Page {i+1} has no extractable text")
            except Exception as e:
                logger.warning(f"Failed to extract text from page {i+1}: {e}")
                continue

        if not pages:
            logger.warning(f"No text could be extracted from PDF: {path}")
            return ""

        full_text = "\n\n".join(pages)
        logger.info(f"Successfully extracted {len(full_text)} characters from {len(pages)} pages")
        return full_text

    except ImportError as e:
        logger.error("PDF library not installed. Please install: pip install pypdf")
        raise ValueError(
            "PDF extraction library not available. Please install pypdf: pip install pypdf"
        ) from e
    except Exception as e:
        logger.error(f"Failed to extract text from PDF {path}: {str(e)}")
        raise ValueError(f"Failed to extract text from PDF: {str(e)}") from e


def extract_slide_texts(text: str) -> List[str]:
    """Naive slide splitter: split on form-feed or double newlines.

    This is intentionally simple for the MVP; better heuristics can be added.
    """
    if not text:
        return []
    # Split on page breaks or long gaps
    slides = [s.strip() for s in text.split('\f') if s.strip()]
    if len(slides) <= 1:
        slides = [s.strip() for s in text.split('\n\n') if s.strip()]
    return slides
