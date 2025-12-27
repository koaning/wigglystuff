function render({model, el}) {
    const parts = model.get("parts") || [];
    const fontSize = model.get("font_size") || 16;
    const displayMode = model.get("display_mode") || false;

    // Load KaTeX CSS and JS if not already loaded
    function loadKaTeX() {
        return new Promise((resolve) => {
            // Check if KaTeX is already loaded
            if (window.katex) {
                resolve();
                return;
            }

            // Load KaTeX CSS
            const cssLink = document.createElement('link');
            cssLink.rel = 'stylesheet';
            cssLink.href = 'https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css';
            cssLink.integrity = 'sha384-n8MVd4RsNIU0tAv4ct0nTaAbDJwPJzDEaqSD1odI+WdtXRGWt2kT6GFkOoRvnM';
            cssLink.crossOrigin = 'anonymous';
            document.head.appendChild(cssLink);

            // Load KaTeX JS
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js';
            script.integrity = 'sha384-XjKyOOzGXjqAgfq6Aw3u6PsHvLa1D9c3qU7DAuU9Dsskk2vvgY0z6U6Cy6u2mz';
            script.crossOrigin = 'anonymous';
            script.onload = resolve;
            document.head.appendChild(script);
        });
    }

    const wrapper = document.createElement('div');
    wrapper.classList.add('latex-formula-wrapper');
    wrapper.style.fontSize = `${fontSize}px`;
    if (displayMode) {
        wrapper.classList.add('latex-formula-display');
    }
    el.appendChild(wrapper);

    function renderFormula() {
        wrapper.innerHTML = '';
        
        if (!window.katex) {
            loadKaTeX().then(() => {
                renderFormula();
            });
            return;
        }

        const container = document.createElement('div');
        container.classList.add('latex-formula-container');
        
        parts.forEach((part, index) => {
            if (!part || part.trim() === '') {
                // Add spacing for empty parts
                const spacer = document.createElement('span');
                spacer.classList.add('latex-formula-spacer');
                spacer.style.display = 'inline-block';
                spacer.style.width = '0.5em';
                container.appendChild(spacer);
                return;
            }

            const partElement = document.createElement('span');
            partElement.classList.add('latex-formula-part');
            
            try {
                window.katex.render(part, partElement, {
                    throwOnError: false,
                    displayMode: displayMode,
                    strict: false,
                });
            } catch (error) {
                // Fallback to plain text if LaTeX rendering fails
                partElement.textContent = part;
                partElement.classList.add('latex-formula-error');
            }
            
            container.appendChild(partElement);
        });

        wrapper.appendChild(container);
    }

    // Initial render
    renderFormula();

    // Update when model changes
    model.on('change:parts', () => {
        renderFormula();
    });

    model.on('change:font_size', () => {
        wrapper.style.fontSize = `${model.get('font_size')}px`;
    });

    model.on('change:display_mode', () => {
        const newDisplayMode = model.get('display_mode');
        if (newDisplayMode) {
            wrapper.classList.add('latex-formula-display');
        } else {
            wrapper.classList.remove('latex-formula-display');
        }
        renderFormula();
    });
}

export default { render };
