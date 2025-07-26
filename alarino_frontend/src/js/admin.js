document.getElementById('bulkUploadForm').addEventListener('submit', async function(event) {
  event.preventDefault();

  const apiKey = document.getElementById('apiKey').value;
  const wordPairsText = document.getElementById('wordPairs').value;
  const isDryRun = document.getElementById('dryRun').checked;
  const resultsSection = document.getElementById('results');
  const successfulUploadsList = document.getElementById('successfulUploads');
  const failedUploadsList = document.getElementById('failedUploads');
  const totalCountSpan = document.getElementById('totalCount');
  const successCountSpan = document.getElementById('successCount');
  const failCountSpan = document.getElementById('failCount');

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

    successfulUploadsList.innerHTML = '';
    failedUploadsList.innerHTML = '';

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

    resultsSection.classList.remove('hidden');

  } catch (error) {
    console.error('Error submitting bulk upload:', error);
    failedUploadsList.innerHTML = `<li>An unexpected error occurred: ${error.message}</li>`;
    totalCountSpan.textContent = pairs.length;
    successCountSpan.textContent = 0;
    failCountSpan.textContent = pairs.length;
    resultsSection.classList.remove('hidden');
  }
});