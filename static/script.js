// --- DOM elementlar ---
const sourceText  = document.getElementById("source-text");
const targetText  = document.getElementById("target-text");
const charCount   = document.getElementById("char-count");
const statsText   = document.getElementById("stats-text");
const clearBtn    = document.getElementById("clear-btn");
const copyBtn     = document.getElementById("copy-btn");

let debounceTimer = null;
let lastTranslated = "";

// --- Belgilar soni ---
function updateCharCount() {
  const len = sourceText.value.length;
  charCount.textContent = len === 0 ? "0 belgi" : `${len} belgi`;
}

// --- Tarjima soʻrovi ---
async function doTranslate() {
  const text = sourceText.value.trim();

  if (!text) {
    showPlaceholder();
    statsText.textContent = "";
    copyBtn.disabled = true;
    lastTranslated = "";
    return;
  }

  try {
    const res = await fetch("/api/translate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });

    if (!res.ok) throw new Error("Server xatosi");

    const data = await res.json();
    lastTranslated = data.translated;

    targetText.innerHTML = "";
    targetText.textContent = data.translated;

    // Statistika
    if (data.total_words > 0) {
      const pct = Math.round((data.translated_count / data.total_words) * 100);
      statsText.textContent =
        `${data.translated_count} / ${data.total_words} soʻz tarjima qilindi (${pct}%)`;
    } else {
      statsText.textContent = "";
    }

    copyBtn.disabled = !data.translated;
  } catch {
    targetText.textContent = "Xato yuz berdi. Serverni tekshiring.";
    copyBtn.disabled = true;
    statsText.textContent = "";
  }
}

function showPlaceholder() {
  targetText.textContent = "";
}

// --- Debounce: 350ms kutgandan soʻng soʻrov yuboriladi ---
function scheduleTranslate() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(doTranslate, 350);
}

// --- Tozalash ---
clearBtn.addEventListener("click", () => {
  sourceText.value = "";
  showPlaceholder();
  charCount.textContent = "0 belgi";
  statsText.textContent = "";
  copyBtn.disabled = true;
  lastTranslated = "";
  sourceText.focus();
});

// --- Nusxalash ---
copyBtn.addEventListener("click", () => {
  if (!lastTranslated) return;
  navigator.clipboard.writeText(lastTranslated).then(() => {
    const orig = copyBtn.textContent;
    copyBtn.textContent = "✓ Nusxalandi";
    setTimeout(() => { copyBtn.textContent = orig; }, 1800);
  });
});

// --- Kiritish hodisasi ---
sourceText.addEventListener("input", () => {
  updateCharCount();
  scheduleTranslate();
});

// --- Sahifa yuklanganda ---
updateCharCount();
