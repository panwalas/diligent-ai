"""
Google Drive integration for downloading pitch deck PDFs.
Supports both public and shared Drive links.
"""
import os
import re
import tempfile
import requests
from typing import Optional


def extract_file_id(drive_url: str) -> Optional[str]:
    """
    Extract Google Drive file ID from various URL formats.

    Supported formats:
    - https://drive.google.com/file/d/FILE_ID/view
    - https://drive.google.com/open?id=FILE_ID
    - https://drive.google.com/uc?id=FILE_ID
    - FILE_ID (raw ID)

    Args:
        drive_url: Google Drive URL or file ID

    Returns:
        File ID or None if not found
    """
    if not drive_url:
        return None

    # Pattern 1: /file/d/FILE_ID/
    match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', drive_url)
    if match:
        return match.group(1)

    # Pattern 2: ?id=FILE_ID or &id=FILE_ID
    match = re.search(r'[?&]id=([a-zA-Z0-9_-]+)', drive_url)
    if match:
        return match.group(1)

    # Pattern 3: Assume it's already a file ID (alphanumeric + dashes/underscores)
    if re.match(r'^[a-zA-Z0-9_-]+$', drive_url.strip()):
        return drive_url.strip()

    return None


def is_drive_link(url: str) -> bool:
    """
    Check if a URL is a Google Drive link.

    Args:
        url: URL to check

    Returns:
        True if it's a Drive link
    """
    if not url:
        return False

    return 'drive.google.com' in url.lower()


def download_from_drive(file_id_or_url: str, output_path: Optional[str] = None) -> str:
    """
    Download a PDF from Google Drive using public/shared link.

    This uses the direct download URL format that works for publicly shared files.
    For private files, you would need OAuth authentication.

    Args:
        file_id_or_url: Google Drive file ID or URL
        output_path: Optional path to save the file. If None, creates temp file.

    Returns:
        Path to downloaded file

    Raises:
        ValueError: If file ID cannot be extracted
        requests.HTTPError: If download fails
    """
    # Extract file ID
    file_id = extract_file_id(file_id_or_url)
    if not file_id:
        raise ValueError(f"Could not extract file ID from: {file_id_or_url}")

    # Create output path if not provided
    if output_path is None:
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, f"{file_id}.pdf")

    # Download URL (works for publicly shared files)
    download_url = f"https://drive.google.com/uc?export=download&id={file_id}"

    # Download the file
    response = requests.get(download_url, stream=True)

    # Check if we got a confirmation page (for large files)
    if 'download_warning' in response.text or 'virus scan warning' in response.text.lower():
        # Extract confirmation token
        confirm_token = None
        for key, value in response.cookies.items():
            if key.startswith('download_warning'):
                confirm_token = value
                break

        if confirm_token:
            download_url = f"https://drive.google.com/uc?export=download&id={file_id}&confirm={confirm_token}"
            response = requests.get(download_url, stream=True)

    # Check for errors
    response.raise_for_status()

    # Check if response is actually a PDF
    content_type = response.headers.get('Content-Type', '')
    if 'text/html' in content_type:
        raise ValueError(
            f"File is not publicly accessible. "
            f"Make sure the Google Drive link is set to 'Anyone with the link can view'. "
            f"File ID: {file_id}"
        )

    # Save to file
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    return output_path


def download_from_drive_with_auth(file_id_or_url: str, credentials_path: str, output_path: Optional[str] = None) -> str:
    """
    Download a PDF from Google Drive using OAuth authentication.
    This method works for private files that require authentication.

    Args:
        file_id_or_url: Google Drive file ID or URL
        credentials_path: Path to Google API credentials JSON file
        output_path: Optional path to save the file

    Returns:
        Path to downloaded file

    Raises:
        ImportError: If google-api-python-client is not installed
        ValueError: If file ID cannot be extracted
    """
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaIoBaseDownload
        import io
    except ImportError:
        raise ImportError(
            "Google API client not installed. "
            "Install with: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
        )

    # Extract file ID
    file_id = extract_file_id(file_id_or_url)
    if not file_id:
        raise ValueError(f"Could not extract file ID from: {file_id_or_url}")

    # Create output path if not provided
    if output_path is None:
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, f"{file_id}.pdf")

    # Load credentials
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    credentials = service_account.Credentials.from_service_account_file(
        credentials_path, scopes=SCOPES
    )

    # Build Drive API service
    service = build('drive', 'v3', credentials=credentials)

    # Download file
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()

    # Write to output file
    with open(output_path, 'wb') as f:
        f.write(fh.getvalue())

    return output_path
