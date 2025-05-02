document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('uploadForm');
    const fileInput = document.getElementById('fileInput');
    const submitBtn = document.getElementById('submitBtn');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const fileTypeIndicator = document.getElementById('fileTypeIndicator');
    const fileTypeSpan = document.getElementById('fileType');
    const summarySection = document.getElementById('summarySection');
    const summaryContent = document.getElementById('summaryContent');
    const factCheckSection = document.getElementById('factCheckSection');
    const trustScore = document.getElementById('trustScore');
    const confidenceLevel = document.getElementById('confidenceLevel');
    const explanation = document.getElementById('explanation');
    const supportingPointsList = document.getElementById('supportingPointsList');
    const contradictoryPointsList = document.getElementById('contradictoryPointsList');
    const rawEvidence = document.getElementById('rawEvidence');

    // Handle file selection
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            const fileType = getFileType(file.name);
            fileTypeSpan.textContent = fileType.charAt(0).toUpperCase() + fileType.slice(1);
            fileTypeIndicator.classList.remove('hidden');
        }
    });

    // Handle form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const file = fileInput.files[0];
        if (!file) {
            alert('Please select a file first');
            return;
        }

        // Show loading indicator
        loadingIndicator.classList.remove('hidden');
        summarySection.classList.add('hidden');
        factCheckSection.classList.add('hidden');

        // Create form data
        const formData = new FormData();
        formData.append('file', file);

        try {
            // Send file to server
            const response = await fetch('/process', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Failed to process file');
            }

            const data = await response.json();

            // Display summary
            summaryContent.textContent = data.summary;
            summarySection.classList.remove('hidden');

            // Display fact-check results
            if (data.factCheck) {
                trustScore.textContent = `${data.factCheck.trust_score}/100`;
                trustScore.style.backgroundColor = getTrustScoreColor(data.factCheck.trust_score);
                
                confidenceLevel.textContent = getConfidenceLevel(data.factCheck.trust_score);
                
                explanation.textContent = data.factCheck.explanation;
                
                // Clear and populate supporting points
                supportingPointsList.innerHTML = '';
                data.factCheck.supporting_points.forEach(point => {
                    const li = document.createElement('li');
                    li.textContent = point;
                    supportingPointsList.appendChild(li);
                });

                // Clear and populate contradictory points
                contradictoryPointsList.innerHTML = '';
                data.factCheck.contradictory_points.forEach(point => {
                    const li = document.createElement('li');
                    li.textContent = point;
                    contradictoryPointsList.appendChild(li);
                });

                // Set raw evidence
                rawEvidence.textContent = data.factCheck.raw_evidence;

                factCheckSection.classList.remove('hidden');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while processing the file. Please try again.');
        } finally {
            loadingIndicator.classList.add('hidden');
        }
    });

    // Helper function to get file type
    function getFileType(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        const types = {
            'mp3': 'audio',
            'wav': 'audio',
            'mp4': 'video',
            'avi': 'video',
            'txt': 'text',
            'pdf': 'text',
            'docx': 'text',
            'jpg': 'image',
            'jpeg': 'image',
            'png': 'image'
        };
        return types[ext] || 'unknown';
    }

    // Helper function to get trust score color
    function getTrustScoreColor(score) {
        if (score >= 70) return 'var(--success-color)';
        if (score >= 40) return 'var(--warning-color)';
        return 'var(--error-color)';
    }

    // Helper function to get confidence level text
    function getConfidenceLevel(score) {
        if (score >= 70) return 'High Confidence';
        if (score >= 40) return 'Moderate Confidence';
        return 'Low Confidence';
    }
}); 