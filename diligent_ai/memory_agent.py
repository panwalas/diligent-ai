"""
Memory Agent for storing and retrieving pitch deck analysis history.
Uses SQLite for structured data and simple similarity matching.
"""
import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path


class MemoryAgent:
    """
    Stores pitch deck analyses and finds similar deals.

    Database schema:
    - deals: Core deal information (id, company_name, analyzed_at, investor_name)
    - claims: Individual claims from each deal
    - questions: Generated questions for each deal
    - metadata: Additional deal metadata (sector, stage, etc.)
    """

    def __init__(self, db_path: str = None):
        """
        Initialize memory agent with SQLite database.

        Args:
            db_path: Path to SQLite database file. Defaults to ./data/memory.db
        """
        if db_path is None:
            # Default to data directory in project root
            db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'memory.db')

        self.db_path = db_path

        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # Initialize database
        self._init_db()

    def _init_db(self):
        """Create database tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Deals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS deals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT,
                pdf_filename TEXT,
                analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                investor_name TEXT,
                founder_email TEXT,
                total_claims INTEGER DEFAULT 0,
                verified_claims INTEGER DEFAULT 0,
                unverified_claims INTEGER DEFAULT 0,
                confidence_avg REAL DEFAULT 0.0
            )
        ''')

        # Claims table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS claims (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deal_id INTEGER,
                claim_text TEXT NOT NULL,
                status TEXT,
                confidence REAL,
                category TEXT,
                evidence_count INTEGER DEFAULT 0,
                FOREIGN KEY (deal_id) REFERENCES deals(id)
            )
        ''')

        # Questions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deal_id INTEGER,
                question_text TEXT NOT NULL,
                priority INTEGER DEFAULT 0,
                FOREIGN KEY (deal_id) REFERENCES deals(id)
            )
        ''')

        # Metadata table (flexible key-value storage)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deal_id INTEGER,
                key TEXT,
                value TEXT,
                FOREIGN KEY (deal_id) REFERENCES deals(id)
            )
        ''')

        # Create indexes for faster queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_deals_company ON deals(company_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_claims_deal ON claims(deal_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_claims_status ON claims(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_questions_deal ON questions(deal_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_metadata_deal ON metadata(deal_id)')

        conn.commit()
        conn.close()

    def store_deal(self, report: Dict[str, Any], company_name: str = None,
                   pdf_filename: str = None, investor_name: str = "Investor",
                   founder_email: str = None) -> int:
        """
        Store a pitch deck analysis in the database.

        Args:
            report: Analysis report from verification pipeline
            company_name: Name of the company (extracted from deck if not provided)
            pdf_filename: Original PDF filename
            investor_name: Name of investor/firm
            founder_email: Founder's email address

        Returns:
            Deal ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        claims = report.get('claims', [])
        questions = report.get('questions', [])

        # Calculate statistics
        total_claims = len(claims)
        verified_claims = sum(1 for c in claims if c.get('status') == 'verified')
        unverified_claims = sum(1 for c in claims if c.get('status') == 'unverified')

        # Calculate average confidence
        confidences = [c.get('confidence', 0) for c in claims if c.get('confidence') is not None]
        confidence_avg = sum(confidences) / len(confidences) if confidences else 0.0

        # Extract company name from claims if not provided
        if not company_name:
            company_name = self._extract_company_name(claims)

        # Insert deal
        cursor.execute('''
            INSERT INTO deals (
                company_name, pdf_filename, investor_name, founder_email,
                total_claims, verified_claims, unverified_claims, confidence_avg
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            company_name, pdf_filename, investor_name, founder_email,
            total_claims, verified_claims, unverified_claims, confidence_avg
        ))

        deal_id = cursor.lastrowid

        # Insert claims
        for claim in claims:
            cursor.execute('''
                INSERT INTO claims (
                    deal_id, claim_text, status, confidence, category, evidence_count
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                deal_id,
                claim.get('claim') or claim.get('text', ''),
                claim.get('status'),
                claim.get('confidence'),
                claim.get('category', 'general'),
                len(claim.get('evidence', []))
            ))

        # Insert questions
        for idx, question in enumerate(questions):
            # Handle both string questions and dict questions
            question_text = question if isinstance(question, str) else question.get('text', str(question))
            cursor.execute('''
                INSERT INTO questions (
                    deal_id, question_text, priority
                ) VALUES (?, ?, ?)
            ''', (deal_id, question_text, idx))

        conn.commit()
        conn.close()

        return deal_id

    def _extract_company_name(self, claims: List[Dict]) -> str:
        """
        Try to extract company name from claims.
        Looks for company/organization mentions in claims.
        """
        # Simple heuristic: look for capitalized words in first few claims
        for claim in claims[:5]:
            text = claim.get('claim') or claim.get('text', '')
            words = text.split()
            for word in words:
                if word.istitle() and len(word) > 2 and word not in ['The', 'We', 'Our', 'This']:
                    return word

        return "Unknown Company"

    def get_similar_deals(self, report: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
        """
        Find similar past deals based on current analysis.

        Uses simple similarity matching based on:
        - Claim text overlap (keyword matching)
        - Verification status patterns
        - Confidence score ranges

        Args:
            report: Current pitch deck analysis
            limit: Maximum number of similar deals to return

        Returns:
            List of similar deals with metadata
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        claims = report.get('claims', [])

        # Extract keywords from current claims
        keywords = self._extract_keywords(claims)

        # Find deals with similar claim keywords
        # This is a simplified similarity - in production, use embeddings/vector search
        similar_deals = []

        # Get all deals
        cursor.execute('''
            SELECT * FROM deals
            ORDER BY analyzed_at DESC
            LIMIT 50
        ''')

        all_deals = cursor.fetchall()

        for deal in all_deals:
            deal_id = deal['id']

            # Get claims for this deal
            cursor.execute('''
                SELECT claim_text, status, confidence
                FROM claims
                WHERE deal_id = ?
            ''', (deal_id,))

            deal_claims = cursor.fetchall()
            deal_keywords = self._extract_keywords([dict(c) for c in deal_claims])

            # Calculate similarity score (simple keyword overlap)
            overlap = len(keywords.intersection(deal_keywords))
            similarity_score = overlap / max(len(keywords), 1)

            # Also consider verification pattern similarity
            deal_verified_ratio = deal['verified_claims'] / max(deal['total_claims'], 1)
            current_verified_ratio = sum(1 for c in claims if c.get('status') == 'verified') / max(len(claims), 1)
            verification_similarity = 1 - abs(deal_verified_ratio - current_verified_ratio)

            # Combined similarity
            combined_score = (similarity_score * 0.7) + (verification_similarity * 0.3)

            if combined_score > 0.1:  # Threshold for relevance
                similar_deals.append({
                    'deal_id': deal_id,
                    'company_name': deal['company_name'],
                    'analyzed_at': deal['analyzed_at'],
                    'total_claims': deal['total_claims'],
                    'verified_claims': deal['verified_claims'],
                    'unverified_claims': deal['unverified_claims'],
                    'confidence_avg': deal['confidence_avg'],
                    'similarity_score': combined_score
                })

        # Sort by similarity and return top N
        similar_deals.sort(key=lambda x: x['similarity_score'], reverse=True)

        conn.close()

        return similar_deals[:limit]

    def _extract_keywords(self, claims: List[Dict]) -> set:
        """
        Extract keywords from claims for similarity matching.
        Simple implementation - in production, use NLP/embeddings.
        """
        keywords = set()

        # Common stop words to ignore
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                      'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
                      'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                      'would', 'should', 'could', 'may', 'might', 'must', 'can'}

        for claim in claims:
            text = claim.get('claim_text') or claim.get('claim') or claim.get('text', '')
            words = text.lower().split()

            for word in words:
                # Clean word (remove punctuation)
                clean_word = ''.join(c for c in word if c.isalnum())

                # Add if not a stop word and length > 3
                if clean_word and len(clean_word) > 3 and clean_word not in stop_words:
                    keywords.add(clean_word)

        return keywords

    def get_all_deals(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get all deals from the database.

        Args:
            limit: Maximum number of deals to return
            offset: Number of deals to skip

        Returns:
            List of deals
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM deals
            ORDER BY analyzed_at DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))

        deals = [dict(row) for row in cursor.fetchall()]

        conn.close()

        return deals

    def get_deal_details(self, deal_id: int) -> Optional[Dict[str, Any]]:
        """
        Get full details for a specific deal including claims and questions.

        Args:
            deal_id: Deal ID

        Returns:
            Deal details or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get deal
        cursor.execute('SELECT * FROM deals WHERE id = ?', (deal_id,))
        deal_row = cursor.fetchone()

        if not deal_row:
            conn.close()
            return None

        deal = dict(deal_row)

        # Get claims
        cursor.execute('SELECT * FROM claims WHERE deal_id = ?', (deal_id,))
        deal['claims'] = [dict(row) for row in cursor.fetchall()]

        # Get questions
        cursor.execute('SELECT * FROM questions WHERE deal_id = ? ORDER BY priority', (deal_id,))
        deal['questions'] = [dict(row) for row in cursor.fetchall()]

        conn.close()

        return deal

    def get_stats(self) -> Dict[str, Any]:
        """
        Get overall statistics across all deals.

        Returns:
            Statistics dict
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total deals
        cursor.execute('SELECT COUNT(*) FROM deals')
        total_deals = cursor.fetchone()[0]

        # Total claims
        cursor.execute('SELECT COUNT(*) FROM claims')
        total_claims = cursor.fetchone()[0]

        # Average verification rate
        cursor.execute('SELECT AVG(verified_claims * 1.0 / NULLIF(total_claims, 0)) FROM deals')
        avg_verification_rate = cursor.fetchone()[0] or 0.0

        # Average confidence
        cursor.execute('SELECT AVG(confidence_avg) FROM deals')
        avg_confidence = cursor.fetchone()[0] or 0.0

        conn.close()

        return {
            'total_deals': total_deals,
            'total_claims': total_claims,
            'avg_verification_rate': round(avg_verification_rate * 100, 1),
            'avg_confidence': round(avg_confidence * 100, 1)
        }
