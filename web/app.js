// Global state
let currentReport = null;

// DOM Elements
const uploadSection = document.getElementById('uploadSection');
const processingSection = document.getElementById('processingSection');
const resultsSection = document.getElementById('resultsSection');
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const browseBtn = document.getElementById('browseBtn');
const founderEmailInput = document.getElementById('founderEmail');
const investorNameInput = document.getElementById('investorName');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
});

function setupEventListeners() {
    // File upload
    browseBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileSelect);

    // Drag and drop
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);

    // Upload method tabs
    document.querySelectorAll('.upload-tab').forEach(btn => {
        btn.addEventListener('click', () => switchUploadMethod(btn.dataset.method));
    });

    // Google Drive link submission
    document.getElementById('analyzeDriveBtn')?.addEventListener('click', handleDriveLinkSubmit);
    document.getElementById('driveLinkInput')?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleDriveLinkSubmit();
    });

    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });

    // Results actions
    document.getElementById('downloadBtn')?.addEventListener('click', downloadReport);
    document.getElementById('newAnalysisBtn')?.addEventListener('click', resetApp);
    document.getElementById('copyEmailBtn')?.addEventListener('click', copyEmail);
}

// File handling
function handleDragOver(e) {
    e.preventDefault();
    uploadArea.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        handleFile(file);
    }
}

function handleFile(file) {
    if (!file.name.endsWith('.pdf')) {
        alert('Please upload a PDF file');
        return;
    }

    processFile(file);
}

// Upload method switching
function switchUploadMethod(method) {
    // Update tab buttons
    document.querySelectorAll('.upload-tab').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.method === method);
    });

    // Show/hide upload methods
    document.getElementById('fileUploadMethod').style.display = method === 'file' ? 'block' : 'none';
    document.getElementById('driveUploadMethod').style.display = method === 'drive' ? 'block' : 'none';
}

// Google Drive link handling
async function handleDriveLinkSubmit() {
    const driveLink = document.getElementById('driveLinkInput').value.trim();

    if (!driveLink) {
        alert('Please enter a Google Drive link');
        return;
    }

    processDriveLink(driveLink);
}

async function processDriveLink(driveLink) {
    const founderEmail = founderEmailInput.value || '';
    const investorName = investorNameInput.value || 'Investor';

    // Show processing section
    showSection('processing');

    // Simulate processing steps with animation
    const steps = [
        { step: 1, message: 'Downloading PDF from Google Drive...', duration: 2000 },
        { step: 2, message: 'Identifying claims in pitch deck...', duration: 3000 },
        { step: 3, message: 'Verifying claims with web evidence...', duration: 4000 },
        { step: 4, message: 'Generating investor questions...', duration: 2000 }
    ];

    try {
        // Start API call
        const apiPromise = fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                drive_link: driveLink,
                founder_email: founderEmail,
                investor_name: investorName
            })
        });

        // Animate steps while waiting for API
        for (const { step, message, duration } of steps) {
            updateProcessingStep(step, message);
            await sleep(duration);
        }

        // Wait for API response
        const response = await apiPromise;

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `API error: ${response.status}`);
        }

        const result = await response.json();
        currentReport = result;

        // Show results
        displayResults(result);

    } catch (error) {
        console.error('Error processing Google Drive link:', error);
        alert(`Error processing pitch deck: ${error.message}`);
        showSection('upload');
    }
}

// API Communication
async function processFile(file) {
    const formData = new FormData();
    formData.append('pdf', file);
    formData.append('founder_email', founderEmailInput.value || '');
    formData.append('investor_name', investorNameInput.value || 'Investor');

    // Show processing section
    showSection('processing');

    // Simulate processing steps with animation
    const steps = [
        { step: 1, message: 'Extracting text from PDF...', duration: 2000 },
        { step: 2, message: 'Identifying claims in pitch deck...', duration: 3000 },
        { step: 3, message: 'Verifying claims with web evidence...', duration: 4000 },
        { step: 4, message: 'Generating investor questions...', duration: 2000 }
    ];

    try {
        // Start API call
        const apiPromise = fetch('/api/analyze', {
            method: 'POST',
            body: formData
        });

        // Animate steps while waiting for API
        for (const { step, message, duration } of steps) {
            updateProcessingStep(step, message);
            await sleep(duration);
        }

        // Wait for API response
        const response = await apiPromise;

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        const result = await response.json();
        currentReport = result;

        // Show results
        displayResults(result);

    } catch (error) {
        console.error('Error processing file:', error);
        alert('Error processing pitch deck. Please try again.');
        showSection('upload');
    }
}

function updateProcessingStep(stepNumber, message) {
    // Update message
    document.getElementById('processingStep').textContent = message;

    // Update step status
    document.querySelectorAll('.step').forEach((step, index) => {
        const stepNum = index + 1;
        const statusEl = step.querySelector('.step-status');

        if (stepNum < stepNumber) {
            step.classList.add('completed');
            step.classList.remove('active');
            statusEl.textContent = 'Completed';
        } else if (stepNum === stepNumber) {
            step.classList.add('active');
            step.classList.remove('completed');
            statusEl.textContent = 'In Progress';
        } else {
            step.classList.remove('active', 'completed');
            statusEl.textContent = 'Pending';
        }
    });
}

// Display results
function displayResults(report) {
    // Update stats
    document.getElementById('totalClaims').textContent = report.claims.length;

    const verified = report.claims.filter(c => c.status === 'verified').length;
    const unverified = report.claims.filter(c => c.status === 'unverified').length;

    document.getElementById('verifiedClaims').textContent = verified;
    document.getElementById('unverifiedClaims').textContent = unverified;
    document.getElementById('questionsGenerated').textContent = report.questions.length;

    // Display similar deals if available
    if (report.similar_deals && report.similar_deals.length > 0) {
        displaySimilarDeals(report.similar_deals);
        document.getElementById('similarDealsSection').style.display = 'block';
    } else {
        document.getElementById('similarDealsSection').style.display = 'none';
    }

    // Display claims
    displayClaims(report.claims);

    // Display questions
    displayQuestions(report.questions);

    // Display email
    document.getElementById('emailContent').textContent = report.email;

    // Show results section
    showSection('results');
}

function displayClaims(claims) {
    const claimsList = document.getElementById('claimsList');
    claimsList.innerHTML = '';

    if (claims.length === 0) {
        claimsList.innerHTML = '<p class="text-secondary">No claims found in the pitch deck.</p>';
        return;
    }

    claims.forEach((claim, index) => {
        const claimCard = document.createElement('div');
        claimCard.className = `claim-card ${claim.status}`;

        const badgeClass = claim.status === 'verified' ? 'badge-verified' :
                          claim.status === 'unverified' ? 'badge-unverified' : 'badge-disputed';
        const badgeText = claim.status.charAt(0).toUpperCase() + claim.status.slice(1);

        const confidence = Math.round(claim.confidence * 100);
        const confidenceColor = confidence >= 70 ? '#10B981' : confidence >= 40 ? '#F59E0B' : '#EF4444';

        claimCard.innerHTML = `
            <div class="claim-header">
                <div class="claim-text">${claim.claim || claim.text || 'No claim text'}</div>
                <span class="claim-badge ${badgeClass}">${badgeText}</span>
            </div>

            <div class="claim-confidence">
                <div class="confidence-bar">
                    <div class="confidence-fill" style="width: ${confidence}%; background-color: ${confidenceColor}"></div>
                </div>
                <span class="confidence-text">${confidence}% confidence</span>
            </div>

            ${claim.evidence && claim.evidence.length > 0 ? `
                <div class="evidence-section">
                    <div class="evidence-title">Evidence:</div>
                    ${claim.evidence.map(ev => `
                        <div class="evidence-item">
                            <div class="evidence-source">${ev.source}</div>
                            <div class="evidence-snippet">${ev.snippet}</div>
                            ${ev.url ? `<a href="${ev.url}" class="evidence-link" target="_blank">View source →</a>` : ''}
                        </div>
                    `).join('')}
                </div>
            ` : ''}
        `;

        claimsList.appendChild(claimCard);
    });
}

function displayQuestions(questions) {
    const questionsList = document.getElementById('questionsList');
    questionsList.innerHTML = '';

    if (questions.length === 0) {
        questionsList.innerHTML = '<p class="text-secondary">No questions generated.</p>';
        return;
    }

    questions.forEach((question, index) => {
        const questionItem = document.createElement('div');
        questionItem.className = 'question-item';
        questionItem.innerHTML = `
            <div class="question-number">${index + 1}</div>
            <div class="question-text">${question}</div>
        `;
        questionsList.appendChild(questionItem);
    });
}

function displaySimilarDeals(similarDeals) {
    const similarDealsList = document.getElementById('similarDealsList');
    similarDealsList.innerHTML = '';

    if (similarDeals.length === 0) {
        similarDealsList.innerHTML = '<p class="text-secondary">No similar deals found in history.</p>';
        return;
    }

    similarDeals.forEach(deal => {
        const dealCard = document.createElement('div');
        dealCard.className = 'similar-deal-card';

        const verificationRate = Math.round((deal.verified_claims / deal.total_claims) * 100);
        const similarityPercent = Math.round(deal.similarity_score * 100);

        // Format date
        const analyzedDate = new Date(deal.analyzed_at);
        const formattedDate = analyzedDate.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });

        dealCard.innerHTML = `
            <div class="similar-deal-header">
                <div class="similar-deal-title">
                    <h4>${deal.company_name || 'Unknown Company'}</h4>
                    <span class="similarity-badge">${similarityPercent}% similar</span>
                </div>
                <div class="similar-deal-date">${formattedDate}</div>
            </div>
            <div class="similar-deal-stats">
                <div class="similar-deal-stat">
                    <span class="stat-label">Claims:</span>
                    <span class="stat-value">${deal.total_claims}</span>
                </div>
                <div class="similar-deal-stat">
                    <span class="stat-label">Verified:</span>
                    <span class="stat-value verified">${deal.verified_claims} (${verificationRate}%)</span>
                </div>
                <div class="similar-deal-stat">
                    <span class="stat-label">Avg Confidence:</span>
                    <span class="stat-value">${Math.round(deal.confidence_avg * 100)}%</span>
                </div>
            </div>
        `;

        similarDealsList.appendChild(dealCard);
    });
}

// Tab switching
function switchTab(tabName) {
    // Update buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });

    // Update content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === `${tabName}Tab`);
    });
}

// Section navigation
function showSection(sectionName) {
    uploadSection.style.display = sectionName === 'upload' ? 'block' : 'none';
    processingSection.style.display = sectionName === 'processing' ? 'block' : 'none';
    resultsSection.style.display = sectionName === 'results' ? 'block' : 'none';
}

// Actions
function downloadReport() {
    if (!currentReport) return;

    const blob = new Blob([JSON.stringify(currentReport, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `diligent-ai-report-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
}

function copyEmail() {
    const emailContent = document.getElementById('emailContent').textContent;
    navigator.clipboard.writeText(emailContent).then(() => {
        const btn = document.getElementById('copyEmailBtn');
        const originalText = btn.textContent;
        btn.textContent = 'Copied!';
        setTimeout(() => {
            btn.textContent = originalText;
        }, 2000);
    });
}

function resetApp() {
    currentReport = null;
    fileInput.value = '';
    showSection('upload');
}

// Utilities
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
