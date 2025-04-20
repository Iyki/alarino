// Fetch the word of the day on page load
document.addEventListener('DOMContentLoaded', fetchWordOfTheDay);

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
      const yorubaWord = result.data.translation[0];
      const englishWord = result.data.source_word;
      
      document.getElementById("dailyYorubaWord").textContent = yorubaWord;
      document.getElementById("dailyEnglishWord").textContent = englishWord;
    } else {
      // Show default word on error
      document.getElementById("dailyYorubaWord").textContent = "ìfé";
      document.getElementById("dailyEnglishWord").textContent = "love";
      console.error("Failed to load word of the day:", result.message);
    }
  } catch (error) {
    // Show default word on error
    document.getElementById("dailyYorubaWord").textContent = "ìfé";
    document.getElementById("dailyEnglishWord").textContent = "love";
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