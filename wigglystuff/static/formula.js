function render({model, el}) {
    // Load KaTeX if not already loaded
    if (!window.katex) {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = 'https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css';
        document.head.appendChild(link);
        
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js';
        script.onload = () => renderFormula();
        document.head.appendChild(script);
    } else {
        renderFormula();
    }

    function renderFormula() {
        const formula = model.get("formula");
        const values = model.get("values");
        const minValues = model.get("min_values");
        const maxValues = model.get("max_values");
        const stepSizes = model.get("step_sizes");
        const digits = model.get("digits");
        const pixelsPerStep = model.get("pixels_per_step");

        // Clear container
        el.innerHTML = '';
        el.classList.add("formula-container");

        // Parse formula to find placeholders
        const placeholderRegex = /\{(\w+)\}/g;
        const parts = [];
        let lastIndex = 0;
        let match;
        
        while ((match = placeholderRegex.exec(formula)) !== null) {
            // Add text before placeholder
            if (match.index > lastIndex) {
                parts.push({
                    type: 'latex',
                    content: formula.substring(lastIndex, match.index)
                });
            }
            // Add placeholder
            parts.push({
                type: 'placeholder',
                name: match[1],
                content: match[0]
            });
            lastIndex = match.index + match[0].length;
        }
        // Add remaining text
        if (lastIndex < formula.length) {
            parts.push({
                type: 'latex',
                content: formula.substring(lastIndex)
            });
        }

        // Create container for formula
        const formulaDiv = document.createElement('div');
        formulaDiv.className = 'formula-display';
        formulaDiv.style.display = 'inline-block';

        // Render each part
        parts.forEach(part => {
            if (part.type === 'latex') {
                if (part.content.trim()) {
                    const latexSpan = document.createElement('span');
                    latexSpan.style.display = 'inline-block';
                    try {
                        katex.render(part.content, latexSpan, {
                            throwOnError: false,
                            displayMode: false,
                        });
                    } catch (e) {
                        console.error('KaTeX rendering error:', e);
                        latexSpan.textContent = part.content;
                    }
                    formulaDiv.appendChild(latexSpan);
                }
            } else if (part.type === 'placeholder') {
                // Create draggable value element
                const valueSpan = document.createElement('span');
                valueSpan.className = 'formula-draggable';
                valueSpan.dataset.placeholder = part.name;
                const value = values[part.name];
                const decimalPlaces = digits[part.name] || 1;
                const formattedValue = value.toFixed(decimalPlaces);
                
                // Set styles before rendering (KaTeX preserves them)
                valueSpan.style.cursor = 'ew-resize';
                valueSpan.style.color = '#0066cc';
                valueSpan.style.textDecoration = 'underline';
                valueSpan.style.userSelect = 'none';
                valueSpan.style.display = 'inline-block';
                valueSpan.style.position = 'relative';
                
                // Render the number with KaTeX for consistent styling
                try {
                    katex.render(formattedValue, valueSpan, {
                        throwOnError: false,
                        displayMode: false,
                    });
                } catch (e) {
                    valueSpan.textContent = formattedValue;
                }
                
                // Ensure all child elements are also styled and clickable
                const allChildren = valueSpan.querySelectorAll('*');
                allChildren.forEach(child => {
                    child.style.pointerEvents = 'none'; // Let clicks bubble to parent
                });
                
                // Add event listener to the span (works for clicks on children too)
                valueSpan.addEventListener('mousedown', startDragging);
                
                formulaDiv.appendChild(valueSpan);
            }
        });

        el.appendChild(formulaDiv);
    }

    function startDragging(e) {
        e.preventDefault();
        e.stopPropagation();
        
        // Find the draggable element (might be clicked on a child element)
        let element = e.target;
        while (element && !element.dataset.placeholder) {
            element = element.parentElement;
        }
        
        if (!element || !element.dataset.placeholder) return;
        
        const placeholderName = element.dataset.placeholder;

        const values = model.get("values");
        const minValues = model.get("min_values");
        const maxValues = model.get("max_values");
        const stepSizes = model.get("step_sizes");
        const digits = model.get("digits");
        const pixelsPerStep = model.get("pixels_per_step");

        const startX = e.clientX;
        const startValue = values[placeholderName];
        const minValue = minValues[placeholderName];
        const maxValue = maxValues[placeholderName];
        const stepSize = stepSizes[placeholderName];
        const decimalPlaces = digits[placeholderName] || 1;

        element.style.cursor = 'grabbing';

        let updateTimeout;
        function debouncedUpdate() {
            clearTimeout(updateTimeout);
            updateTimeout = setTimeout(() => {
                model.save_changes();
            }, 50);
        }

        function onMouseMove(e) {
            const deltaX = e.clientX - startX;
            const steps = Math.floor(deltaX / pixelsPerStep);
            const newValue = Math.max(
                minValue,
                Math.min(maxValue, startValue + steps * stepSize)
            );
            
            // Update values
            const updatedValues = {...values};
            updatedValues[placeholderName] = parseFloat(newValue.toFixed(10));
            model.set("values", updatedValues);
            
            // Re-render formula with new value
            renderFormula();
            debouncedUpdate();
        }

        function onMouseUp() {
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
            model.save_changes();
        }

        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
    }

    // Listen for model changes
    model.on('change:formula', () => {
        if (window.katex) renderFormula();
    });
    model.on('change:values', () => {
        if (window.katex) renderFormula();
    });
    model.on('change:min_values', () => {
        if (window.katex) renderFormula();
    });
    model.on('change:max_values', () => {
        if (window.katex) renderFormula();
    });
    model.on('change:step_sizes', () => {
        if (window.katex) renderFormula();
    });
    model.on('change:digits', () => {
        if (window.katex) renderFormula();
    });

    // Initial render
    if (window.katex) {
        renderFormula();
    }
}

export default { render };
