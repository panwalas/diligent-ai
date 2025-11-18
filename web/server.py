"""
Flask web server for Diligent AI.
Serves the web UI and provides API endpoints for pitch deck analysis.
"""
import os
import sys
import tempfile
import logging
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

# Add parent directory to path to import diligent_ai module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from diligent_ai.cli import run
from diligent_ai.config import load_config
from diligent_ai.drive_utils import download_from_drive, is_drive_link
from diligent_ai.memory_agent import MemoryAgent

# Initialize memory agent
memory = MemoryAgent()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder='.')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf'}


def allowed_file(filename):
    """Check if file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Serve the main index.html page."""
    return send_from_directory('.', 'index.html')


@app.route('/<path:path>')
def static_files(path):
    """Serve static files (CSS, JS)."""
    return send_from_directory('.', path)


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """
    Analyze a pitch deck PDF.

    Accepts two input methods:
    1. File upload (multipart/form-data):
       - pdf: PDF file
       - founder_email: Optional founder email
       - investor_name: Optional investor name

    2. Google Drive link (JSON):
       - drive_link: Google Drive URL or file ID
       - founder_email: Optional founder email
       - investor_name: Optional investor name

    Returns JSON report with claims, questions, and email.
    """
    try:
        # Check if this is a Google Drive link submission (JSON)
        if request.is_json:
            data = request.get_json()
            drive_link = data.get('drive_link')

            if not drive_link:
                return jsonify({'error': 'No drive_link provided'}), 400

            # Get optional parameters
            founder_email = data.get('founder_email', None)
            investor_name = data.get('investor_name', 'Investor')

            # Sanitize inputs
            if founder_email:
                founder_email = founder_email.strip()
                if not founder_email or len(founder_email) > 100:
                    founder_email = None

            if investor_name:
                investor_name = investor_name.strip()
                if not investor_name or len(investor_name) > 50:
                    investor_name = 'Investor'

            logger.info(f"Processing Google Drive link: {drive_link}, founder_email={founder_email}, investor_name={investor_name}")

            # Download from Google Drive
            try:
                temp_path = download_from_drive(drive_link)
                logger.info(f"Downloaded PDF from Drive to: {temp_path}")
            except ValueError as e:
                logger.error(f"Failed to download from Drive: {e}")
                return jsonify({'error': str(e)}), 400
            except Exception as e:
                logger.error(f"Error downloading from Drive: {e}")
                return jsonify({'error': f'Failed to download from Google Drive: {str(e)}'}), 500

            try:
                # Find config file
                config_path = os.path.join(os.path.dirname(__file__), '..', '.config.yaml')
                if not os.path.exists(config_path):
                    logger.warning(f"Config file not found at {config_path}, using defaults")
                    config_path = None

                # Run analysis
                report = run(
                    pdf_path=temp_path,
                    config_path=config_path,
                    founder_email=founder_email,
                    investor_name=investor_name,
                    print_output=False
                )

                logger.info(f"Analysis complete. Found {len(report.get('claims', []))} claims, {len(report.get('questions', []))} questions")

                # Find similar deals BEFORE storing this one
                similar_deals = memory.get_similar_deals(report, limit=3)
                report['similar_deals'] = similar_deals

                # Store in memory agent
                try:
                    deal_id = memory.store_deal(
                        report=report,
                        pdf_filename=drive_link,
                        investor_name=investor_name,
                        founder_email=founder_email
                    )
                    logger.info(f"Stored deal in memory with ID: {deal_id}")
                    report['deal_id'] = deal_id
                except Exception as e:
                    logger.warning(f"Failed to store deal in memory: {e}")

                return jsonify(report), 200

            finally:
                # Clean up temporary file
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                        # Also remove temp directory if it's empty
                        temp_dir = os.path.dirname(temp_path)
                        if os.path.isdir(temp_dir) and not os.listdir(temp_dir):
                            os.rmdir(temp_dir)
                    logger.debug(f"Cleaned up temporary file: {temp_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary file {temp_path}: {e}")

        # Handle file upload (multipart/form-data)
        # Validate request has file
        if 'pdf' not in request.files:
            logger.warning("No PDF file in request")
            return jsonify({'error': 'No PDF file provided'}), 400

        file = request.files['pdf']

        # Validate filename
        if file.filename == '':
            logger.warning("Empty filename")
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            logger.warning(f"Invalid file type: {file.filename}")
            return jsonify({'error': 'Only PDF files are allowed'}), 400

        # Get optional parameters
        founder_email = request.form.get('founder_email', None)
        investor_name = request.form.get('investor_name', 'Investor')

        # Sanitize founder_email (basic validation)
        if founder_email:
            founder_email = founder_email.strip()
            if not founder_email or len(founder_email) > 100:
                founder_email = None

        # Sanitize investor_name
        if investor_name:
            investor_name = investor_name.strip()
            if not investor_name or len(investor_name) > 50:
                investor_name = 'Investor'

        logger.info(f"Processing PDF: {file.filename}, founder_email={founder_email}, investor_name={investor_name}")

        # Save uploaded file to temporary location
        temp_dir = tempfile.mkdtemp()
        filename = secure_filename(file.filename)
        temp_path = os.path.join(temp_dir, filename)

        try:
            file.save(temp_path)
            logger.info(f"Saved PDF to temporary file: {temp_path}")

            # Find config file (look in project root)
            config_path = os.path.join(os.path.dirname(__file__), '..', '.config.yaml')
            if not os.path.exists(config_path):
                logger.warning(f"Config file not found at {config_path}, using defaults")
                config_path = None

            # Run analysis (don't print to stdout when called from API)
            report = run(
                pdf_path=temp_path,
                config_path=config_path,
                founder_email=founder_email,
                investor_name=investor_name,
                print_output=False
            )

            logger.info(f"Analysis complete. Found {len(report.get('claims', []))} claims, {len(report.get('questions', []))} questions")

            # Find similar deals BEFORE storing this one
            similar_deals = memory.get_similar_deals(report, limit=3)
            report['similar_deals'] = similar_deals

            # Store in memory agent
            try:
                deal_id = memory.store_deal(
                    report=report,
                    pdf_filename=filename,
                    investor_name=investor_name,
                    founder_email=founder_email
                )
                logger.info(f"Stored deal in memory with ID: {deal_id}")
                report['deal_id'] = deal_id
            except Exception as e:
                logger.warning(f"Failed to store deal in memory: {e}")

            return jsonify(report), 200

        finally:
            # Clean up temporary file
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                os.rmdir(temp_dir)
                logger.debug(f"Cleaned up temporary file: {temp_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file {temp_path}: {e}")

    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to process PDF',
            'message': str(e)
        }), 500


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'diligent-ai'
    }), 200


@app.route('/api/deals', methods=['GET'])
def get_deals():
    """
    Get all deals from memory.

    Query params:
    - limit: Number of deals to return (default: 20)
    - offset: Number of deals to skip (default: 0)

    Returns:
    - List of deals with summary information
    """
    try:
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))

        # Validate limits
        limit = min(limit, 100)  # Max 100 at a time
        offset = max(offset, 0)

        deals = memory.get_all_deals(limit=limit, offset=offset)

        return jsonify({
            'deals': deals,
            'limit': limit,
            'offset': offset,
            'count': len(deals)
        }), 200

    except Exception as e:
        logger.error(f"Error fetching deals: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to fetch deals'}), 500


@app.route('/api/deals/<int:deal_id>', methods=['GET'])
def get_deal(deal_id):
    """
    Get full details for a specific deal.

    Args:
        deal_id: Deal ID

    Returns:
        Full deal details including claims and questions
    """
    try:
        deal = memory.get_deal_details(deal_id)

        if not deal:
            return jsonify({'error': 'Deal not found'}), 404

        return jsonify(deal), 200

    except Exception as e:
        logger.error(f"Error fetching deal {deal_id}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to fetch deal'}), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """
    Get overall statistics across all deals.

    Returns:
        Statistics summary
    """
    try:
        stats = memory.get_stats()
        return jsonify(stats), 200

    except Exception as e:
        logger.error(f"Error fetching stats: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to fetch stats'}), 500


if __name__ == '__main__':
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5000))

    logger.info(f"Starting Diligent AI web server on port {port}")
    logger.info(f"Open http://localhost:{port} in your browser")

    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=port,
        debug=True
    )
