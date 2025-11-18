"""
Unit tests for PDF extraction utilities.
"""
import os
import pytest
from diligent_ai.pdf_utils import extract_text_from_pdf, extract_slide_texts


class TestPDFExtraction:
    """Tests for PDF text extraction."""

    def test_extract_text_from_valid_pdf(self):
        """Test extracting text from a valid PDF file."""
        pdf_path = os.path.join(os.path.dirname(__file__), "..", "example", "sample.pdf")
        text = extract_text_from_pdf(pdf_path)

        assert text is not None
        assert isinstance(text, str)
        assert len(text) > 100  # Should have substantial content
        # Check for known content from Peekly deck
        assert "Peekly" in text or "peekly" in text.lower()

    def test_extract_text_nonexistent_file(self):
        """Test that FileNotFoundError is raised for nonexistent files."""
        with pytest.raises(FileNotFoundError) as exc_info:
            extract_text_from_pdf("nonexistent.pdf")

        assert "does not exist" in str(exc_info.value)

    def test_extract_text_directory_instead_of_file(self):
        """Test that ValueError is raised when path is a directory."""
        test_dir = os.path.dirname(__file__)
        with pytest.raises(ValueError) as exc_info:
            extract_text_from_pdf(test_dir)

        assert "not a file" in str(exc_info.value)

    def test_extract_text_non_pdf_file(self):
        """Test warning when file doesn't have .pdf extension."""
        # This should still try to process but might fail or warn
        # We're just checking it doesn't crash on extension check
        test_file = __file__  # This Python file
        try:
            # May raise ValueError for invalid PDF format, which is expected
            extract_text_from_pdf(test_file)
        except ValueError as e:
            # Expected to fail as it's not a PDF
            assert "Failed to extract" in str(e) or "PDF" in str(e)


class TestSlideExtraction:
    """Tests for slide text extraction."""

    def test_extract_slides_with_form_feeds(self):
        """Test slide extraction with form-feed characters."""
        text = "Slide 1\fSlide 2\fSlide 3"
        slides = extract_slide_texts(text)

        assert len(slides) == 3
        assert "Slide 1" in slides[0]
        assert "Slide 2" in slides[1]
        assert "Slide 3" in slides[2]

    def test_extract_slides_with_double_newlines(self):
        """Test slide extraction with double newlines."""
        text = "Slide 1\n\nSlide 2\n\nSlide 3"
        slides = extract_slide_texts(text)

        assert len(slides) >= 3  # Should split into at least 3 parts

    def test_extract_slides_empty_text(self):
        """Test slide extraction with empty text."""
        slides = extract_slide_texts("")
        assert slides == []

    def test_extract_slides_none_text(self):
        """Test slide extraction with None."""
        slides = extract_slide_texts(None)
        assert slides == []

    def test_extract_slides_single_slide(self):
        """Test slide extraction with single slide (no separators)."""
        text = "This is a single slide with no separators"
        slides = extract_slide_texts(text)

        assert len(slides) >= 1
        assert "single slide" in slides[0]
