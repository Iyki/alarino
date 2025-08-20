document.getElementById('bulkUploadForm').addEventListener('submit', async function(event) {
  event.preventDefault();

  const apiKey = document.getElementById('apiKey').value;
  const wordPairsText = document.getElementById('wordPairs').value;
  const isDryRun = document.getElementById('dryRun').checked;
  const resultsSection = document.getElementById('results');
  const loadingIndicator = document.getElementById('loadingIndicator');
  const resultsContent = document.getElementById('resultsContent');
  const successfulUploadsList = document.getElementById('successfulUploads');
  const failedUploadsList = document.getElementById('failedUploads');
  const totalCountSpan = document.getElementById('totalCount');
  const successCountSpan = document.getElementById('successCount');
  const failCountSpan = document.getElementById('failCount');

  // Clear previous results and show loading indicator
  resultsSection.classList.remove('hidden');
  loadingIndicator.classList.remove('hidden');
  resultsContent.classList.add('hidden');
  successfulUploadsList.innerHTML = '';
  failedUploadsList.innerHTML = '';
  totalCountSpan.textContent = '0';
  successCountSpan.textContent = '0';
  failCountSpan.textContent = '0';

  const payload = {
    text_input: wordPairsText,
    dry_run: isDryRun
  };

  try {
    const response = await fetch('/api/admin/bulk-upload', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify(payload)
    });

    const result = await response.json();

    if (response.ok) {
      result.data.successful_pairs.forEach(item => {
        const li = document.createElement('li');
        li.textContent = `${item.english}, ${item.yoruba}`;
        successfulUploadsList.appendChild(li);
      });

      result.data.failed_pairs.forEach(item => {
        const li = document.createElement('li');
        li.textContent = `${item.line} - Reason: ${item.reason}`;
        failedUploadsList.appendChild(li);
      });

      totalCountSpan.textContent = result.data.successful_pairs.length + result.data.failed_pairs.length;
      successCountSpan.textContent = result.data.successful_pairs.length;
      failCountSpan.textContent = result.data.failed_pairs.length;

    } else {
      const li = document.createElement('li');
      li.textContent = `Error: ${result.message || 'An unknown error occurred.'}`;
      failedUploadsList.appendChild(li);
      const pairCount = wordPairsText.split('\n').filter(line => line.trim() !== '').length;
      totalCountSpan.textContent = pairCount;
      successCountSpan.textContent = 0;
      failCountSpan.textContent = pairCount;
    }

  } catch (error) {
    console.error('Error submitting bulk upload:', error);
    failedUploadsList.innerHTML = `<li>An unexpected error occurred: ${error.message}</li>`;
    const pairCount = wordPairsText.split('\n').filter(line => line.trim() !== '').length;
    totalCountSpan.textContent = pairCount;
    successCountSpan.textContent = 0;
    failCountSpan.textContent = pairCount;
  } finally {
    // Hide loading indicator and show results
    loadingIndicator.classList.add('hidden');
    resultsContent.classList.remove('hidden');
  }
});