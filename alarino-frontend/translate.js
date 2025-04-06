
function translateWord() {
    const input = document.getElementById("englishWord").value.toLowerCase();
    const resultBox = document.getElementById("translationResult");

    if (input === "water") {
      resultBox.innerHTML = `
        <p class="text-xl font-bold">water</p>
        <p class="italic text-gray-700">omi <span class="not-italic text-sm text-gray-500">n. noo</span></p>
        <p class="mt-2 text-gray-600">A clear liquid that falls as rain.</p>`;
    } else {
      resultBox.innerHTML = `
        <p class="text-xl font-bold">${input}</p>
        <p class="italic text-gray-700">(no translation found)</p>
        <p class="mt-2 text-gray-600">We're still learning — try another word!</p>`;
    }
  }