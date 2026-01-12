function render({ model, el }) {
    const container = document.createElement("div");
    container.className = "text-compare-container";

    const panelA = document.createElement("div");
    panelA.className = "text-compare-panel";

    const panelB = document.createElement("div");
    panelB.className = "text-compare-panel";

    container.appendChild(panelA);
    container.appendChild(panelB);
    el.appendChild(container);

    function tokenize(text) {
        // Split into words while preserving whitespace info
        const words = [];
        const regex = /(\S+)(\s*)/g;
        let match;
        while ((match = regex.exec(text)) !== null) {
            words.push({ word: match[1], space: match[2] });
        }
        return words;
    }

    function buildMatchRanges(matches, side) {
        // Build a map of word indices that belong to each match
        const wordToMatch = new Map();
        matches.forEach((m, idx) => {
            const start = side === "a" ? m.start_a : m.start_b;
            const end = side === "a" ? m.end_a : m.end_b;
            for (let i = start; i < end; i++) {
                wordToMatch.set(i, idx);
            }
        });
        return wordToMatch;
    }

    function renderPanel(panel, text, matches, side, otherPanel) {
        panel.innerHTML = "";
        const tokens = tokenize(text);
        const wordToMatch = buildMatchRanges(matches, side);
        const selectedMatch = model.get("selected_match");

        let currentMatchIdx = null;
        let currentSpan = null;

        tokens.forEach((token, wordIdx) => {
            const matchIdx = wordToMatch.get(wordIdx);

            if (matchIdx !== currentMatchIdx) {
                // Close previous span if any
                if (currentSpan) {
                    panel.appendChild(currentSpan);
                    currentSpan = null;
                }

                if (matchIdx !== undefined) {
                    // Start new match span
                    currentSpan = document.createElement("span");
                    currentSpan.className = "text-compare-match";
                    currentSpan.dataset.matchIndex = matchIdx;
                    if (matchIdx === selectedMatch) {
                        currentSpan.classList.add("selected");
                    }

                    // Hover handlers
                    currentSpan.addEventListener("mouseenter", () => {
                        model.set("selected_match", matchIdx);
                        model.save_changes();
                    });

                    currentSpan.addEventListener("mouseleave", () => {
                        model.set("selected_match", -1);
                        model.save_changes();
                    });
                }
                currentMatchIdx = matchIdx;
            }

            // Create text node for this word
            const textNode = document.createTextNode(token.word + token.space);

            if (currentSpan) {
                currentSpan.appendChild(textNode);
            } else {
                panel.appendChild(textNode);
            }
        });

        // Close final span if any
        if (currentSpan) {
            panel.appendChild(currentSpan);
        }
    }

    function updateSelection() {
        const selectedMatch = model.get("selected_match");

        // Update classes on all match spans
        container.querySelectorAll(".text-compare-match").forEach(span => {
            const idx = parseInt(span.dataset.matchIndex, 10);
            if (idx === selectedMatch) {
                span.classList.add("selected");
            } else {
                span.classList.remove("selected");
            }
        });
    }

    function fullRender() {
        const textA = model.get("text_a");
        const textB = model.get("text_b");
        const matches = model.get("matches");

        renderPanel(panelA, textA, matches, "a", panelB);
        renderPanel(panelB, textB, matches, "b", panelA);
    }

    // Initial render
    fullRender();

    // Listen for changes
    model.on("change:text_a", fullRender);
    model.on("change:text_b", fullRender);
    model.on("change:matches", fullRender);
    model.on("change:selected_match", updateSelection);
}

export default { render };
