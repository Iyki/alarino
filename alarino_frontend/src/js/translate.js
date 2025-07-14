// Fetch the word of the day on page load
document.addEventListener('DOMContentLoaded', function() {
  fetchWordOfTheDay();
  fetchRandomProverb();
  
  const nextProverbBtn = document.getElementById("next-proverb-btn");
  if (nextProverbBtn) {
    nextProverbBtn.addEventListener("click", fetchRandomProverb);
  }
  
  let englishWordInput = null;
  let wordToTranslate = null;
  
  // First, check if the URL path contains a word (priority)
  const pathParts = window.location.pathname.split('/');
  if (pathParts.length > 2 && pathParts[1] === 'word') {
    wordToTranslate = decodeURIComponent(pathParts[2]);
    englishWordInput = document.getElementById('englishWord');
    if (englishWordInput) {
      englishWordInput.value = wordToTranslate;
      updatePageMetadata(wordToTranslate);
  }
  } 
  // If no word in path, check for query parameter as fallback
  else {
    const urlParams = new URLSearchParams(window.location.search);
    const wordParam = urlParams.get('word');
    
    if (wordParam) {
      wordToTranslate = decodeURIComponent(wordParam);
      englishWordInput = document.getElementById('englishWord');
      if (englishWordInput) {
        englishWordInput.value = wordToTranslate;
      }
    }
  }
  
  // If we found a word through either method, trigger translation
  if (englishWordInput && wordToTranslate) {
    // Trigger translation after a short delay
    setTimeout(() => translateWord(), 2);
    highlightTranslateBox();
  }
});

function toggleDailyTranslation() {
  const englishWord = document.getElementById("dailyEnglishWord");
  const viewBtn = document.getElementById("viewTranslationBtn");
  
  if (englishWord.classList.contains("hidden")) {
    englishWord.classList.remove("hidden");
    viewBtn.textContent = "Hide translation";
  } else {
    englishWord.classList.add("hidden");
    viewBtn.textContent = "View translation";
  }
}

async function fetchWordOfTheDay() {
  try {
    const response = await fetch(`${window.ALARINO_CONFIG.apiBaseUrl}/daily-word`);
    const result = await response.json();
    
    if (result.success) {
      const yorubaWord = result.data.yoruba_word;
      const englishWord = result.data.english_word;
      
      document.getElementById("dailyYorubaWord").textContent = yorubaWord;
      document.getElementById("dailyEnglishWord").textContent = englishWord;
    } else {
      console.error("Failed to load word of the day:", result.message);
    }
  } catch (error) {
    console.error("Failed to fetch word of the day:", error);
  }
}

async function translateWord() {
  const input = document.getElementById("englishWord").value.toLowerCase().trim();

  const wordLabel = document.getElementById("wordLabel");
  const wordYoruba = document.getElementById("wordYoruba");
  const wordDefinition = document.getElementById("wordDefinition");

  if (!input) return;
  
  try {
    const response = await fetch(`${window.ALARINO_CONFIG.apiBaseUrl}/translate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        text: input,
        source_lang: "en",
        target_lang: "yo",
      }),
    });

    const result = await response.json();

    if (result.success) {
      const translation = result.data.translation
        .map((line) => `<p>${line}</p>`) // One per line
        .join("");
      wordLabel.textContent = result.data.source_word;
      wordYoruba.innerHTML = translation;
      wordDefinition.textContent = "";
      
      // Update URL to reflect the current word (without reloading the page)
      updatePageUrl(result.data.source_word);
    } else {
      wordLabel.textContent = input;
      wordYoruba.textContent = "(no translation found)";
      wordDefinition.textContent = "We're still learning — try another word!";
    }
  } catch (error) {
    wordLabel.textContent = input;
    wordYoruba.textContent = "(error fetching translation)";
    wordDefinition.textContent = "Please check your connection or try again later.";
  }
}

function updatePageUrl(word) {
    // Update the URL without refreshing the page
  const newUrl = `/word/${encodeURIComponent(word.toLowerCase())}`;
  if (window.location.pathname !== newUrl) {
    window.history.pushState({ word: word }, '', newUrl);
    document.title = `${word} in Yoruba | Alarino Dictionary`;
    // window.location.href = newUrl; // This causes a page reload instead of history manipulation
    updatePageMetadata(word);
  }
}

function updatePageMetadata(word) {
  // Capitalize first letter for title
  const capitalizedWord = word.charAt(0).toUpperCase() + word.slice(1);
  
  // Update page title
  const pageTitle = document.getElementById("page-title");
  if (pageTitle) {
    pageTitle.textContent = `${capitalizedWord} in Yoruba | Alarino Dictionary`;
  } else {
    document.title = `${capitalizedWord} in Yoruba | Alarino Dictionary`;
  }
  
  // Update meta description
  const metaDescription = document.getElementById("meta-description");
  if (metaDescription) {
    metaDescription.setAttribute("content", 
      `What is "${word}" in Yoruba? Find the Yoruba translation for "${word}" on Alarino - the English to Yoruba Dictionary.`);
  }
  
  // Update canonical link
  const canonicalLink = document.getElementById("canonical-link");
  if (canonicalLink) {
    canonicalLink.setAttribute("href", 
      `${window.ALARINO_CONFIG.baseUrl}/word/${encodeURIComponent(word.toLowerCase())}`);
  }
}

function highlightTranslateBox() {
  const box = document.getElementById("translateBox");
  box.classList.add("ring", "ring-yellow-400");
  setTimeout(() => {
    box.classList.remove("ring", "ring-yellow-400");
  }, 2000);
  
  // Also scroll to the translate box
  box.scrollIntoView({ behavior: 'smooth' });
}

// Modal functions
function openAddWordModal() {
  document.getElementById("addWordModal").classList.remove("hidden");
  document.body.classList.add("overflow-hidden"); // Prevent scrolling behind modal
}

function closeAddWordModal() {
  document.getElementById("addWordModal").classList.add("hidden");
  document.body.classList.remove("overflow-hidden"); // Re-enable scrolling
}

function openFeedbackModal() {
  document.getElementById("feedbackModal").classList.remove("hidden");
  document.body.classList.add("overflow-hidden"); // Prevent scrolling behind modal
}

function closeFeedbackModal() {
  document.getElementById("feedbackModal").classList.add("hidden");
  document.body.classList.remove("overflow-hidden"); // Re-enable scrolling
}

// Close modal when clicking outside
window.onclick = function(event) {
  const addWordModal = document.getElementById("addWordModal");
  const feedbackModal = document.getElementById("feedbackModal");
  
  if (event.target == addWordModal) {
    closeAddWordModal();
  }
  
  if (event.target == feedbackModal) {
    closeFeedbackModal();
  }
}

// Handle browser back button
window.onpopstate = function(event) {
  if (event.state && event.state.word) {
    const englishWordInput = document.getElementById('englishWord');
    if (englishWordInput) {
      englishWordInput.value = event.state.word;
      translateWord();
    }
  }
};

async function fetchRandomProverb() {
  const proverbYoruba = document.getElementById("proverb-yoruba");
  const proverbEnglish = document.getElementById("proverb-english");

  try {
    const response = await fetch(`${window.ALARINO_CONFIG.apiBaseUrl}/proverb`);
    const result = await response.json();

    if (result.success) {
      proverbYoruba.textContent = result.data.yoruba_text;
      proverbEnglish.textContent = result.data.english_text;
    } else {
      console.error("Failed to load proverb:", result.message);
    }
  } catch (error) {
    console.error("Failed to fetch proverb:", error);
    proverbYoruba.textContent = "Error fetching proverb.";
    proverbEnglish.textContent = "Please check your connection or try again later.";
  }
}