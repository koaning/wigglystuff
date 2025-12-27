function render({model, el}) {
    // Note: This widget only supports simple formulas where placeholders
    // are outside LaTeX structures. For complex cases like matrices/vectors
    // with placeholders inside, a different approach would be needed.
    renderFormula();

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

        // Parse formula into parts: LaTeX text and placeholders
        const placeholderRegex = /\{(\w+)\}/g;
        const parts = [];
        let lastIndex = 0;
        let match;
        
        while ((match = placeholderRegex.exec(formula)) !== null) {
            // Add LaTeX text before placeholder
            if (match.index > lastIndex) {
                parts.push({
                    type: 'latex',
                    content: formula.substring(lastIndex, match.index)
                });
            }
            // Add placeholder
            parts.push({
                type: 'placeholder',
                name: match[1]
            });
            lastIndex = match.index + match[0].length;
        }
        // Add remaining LaTeX text
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
                    // For LaTeX parts, just display as text for now
                    // In a real implementation, you'd need KaTeX available
                    const latexSpan = document.createElement('span');
                    latexSpan.style.display = 'inline-block';
                    latexSpan.style.fontFamily = 'serif';
                    latexSpan.style.fontStyle = 'italic';
                    latexSpan.textContent = part.content;
                    formulaDiv.appendChild(latexSpan);
                }
            } else if (part.type === 'placeholder') {
                // Create draggable value element as plain HTML
                const placeholderName = part.name;
                const value = values[placeholderName];
                const decimalPlaces = digits[placeholderName] || 1;
                const formattedValue = value.toFixed(decimalPlaces);
                
                const valueSpan = document.createElement('span');
                valueSpan.className = 'formula-draggable';
                valueSpan.dataset.placeholder = placeholderName;
                valueSpan.style.cursor = 'ew-resize';
                valueSpan.style.color = '#0066cc';
                valueSpan.style.textDecoration = 'underline';
                valueSpan.style.userSelect = 'none';
                valueSpan.style.display = 'inline-block';
                valueSpan.style.fontFamily = 'serif';
                valueSpan.style.fontStyle = 'italic';
                valueSpan.textContent = formattedValue;
                
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
    model.on('change:formula', renderFormula);
    model.on('change:values', renderFormula);
    model.on('change:min_values', renderFormula);
    model.on('change:max_values', renderFormula);
    model.on('change:step_sizes', renderFormula);
    model.on('change:digits', renderFormula);

    // Initial render
    renderFormula();
}

export default { render };
