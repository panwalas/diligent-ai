import argparse
import json
import logging
import sys
from .pdf_utils import extract_text_from_pdf, extract_slide_texts
from .llm_client import LLMClient
from .verifier import extract_claims_from_text, verify_claims
from .agent import generate_questions, compose_email, generate_summary
from .config import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)  # Log to stderr so JSON output stays clean on stdout
    ]
)
logger = logging.getLogger(__name__)


def run(pdf_path: str, config_path: str = None, founder_email: str = None, investor_name: str = "Investor", print_output: bool = True):
    """Run the full due diligence pipeline on a pitch deck PDF.

    Args:
        pdf_path: Path to the pitch deck PDF file
        config_path: Path to config YAML file (optional)
        founder_email: Email address of founder (optional)
        investor_name: Name of investor for email template (default: "Investor")
        print_output: Whether to print JSON to stdout (default: True, set False when calling from API)

    Returns:
        Dict containing claims, questions, and email template

    Raises:
        FileNotFoundError: If PDF file doesn't exist
        ValueError: If PDF extraction or processing fails
    """
    try:
        logger.info(f"Loading config from: {config_path or '.config.yaml'}")
        cfg = load_config(config_path)
        llm = LLMClient(config_path)

        logger.info(f"Extracting text from PDF: {pdf_path}")
        text = extract_text_from_pdf(pdf_path)

        slides = extract_slide_texts(text)
        logger.info(f"Found {len(slides)} slides (approx). Running claim extraction...")

        claims = extract_claims_from_text(text, llm)
        logger.info(f"Extracted {len(claims)} claims. Verifying...")

        verified = verify_claims(claims, llm, cfg_path=config_path)
        logger.info("Verification complete. Generating summary and investor questions...")

        summary = generate_summary(verified, llm)
        logger.info("Summary generated. Generating questions...")

        questions = generate_questions(verified, llm, user_profile=cfg.get("user"))

        email = compose_email(questions, founder_email or "founder@example.com", investor_name, summary=summary)

        report = {
            "summary": summary,
            "claims": verified,
            "questions": questions,
            "email": email
        }

        # Output JSON to stdout (only when running from CLI)
        if print_output:
            print(json.dumps(report, indent=2))
        logger.info("Due diligence report generated successfully")

        return report

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Processing error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser("diligent-ai")
    parser.add_argument("pdf", help="Path to the pitch deck PDF")
    parser.add_argument("--config", help="Path to .config.yaml", default=None)
    parser.add_argument("--founder-email", help="Founder's email to compose to", default=None)
    parser.add_argument("--investor-name", help="Investor name for email", default="Investor")
    args = parser.parse_args()
    run(args.pdf, config_path=args.config, founder_email=args.founder_email, investor_name=args.investor_name)


if __name__ == "__main__":
    main()
