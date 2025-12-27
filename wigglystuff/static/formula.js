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

        // Build LaTeX string with values substituted
        // We'll use a unique class name via \class that we can find later
        let latexString = formula;
        const placeholderMap = {}; // Maps formatted value -> placeholder name
        
        Object.keys(values).forEach(placeholderName => {
            const value = values[placeholderName];
            const decimalPlaces = digits[placeholderName] || 1;
            const formattedValue = value.toFixed(decimalPlaces);
            
            // Replace placeholder with formatted value wrapped in a special class
            // Use \class to add a data attribute we can find
            const placeholderRegex = new RegExp(`\\{${placeholderName}\\}`, 'g');
            // Use \textcolor and \class for styling and identification
            latexString = latexString.replace(
                placeholderRegex,
                `\\textcolor{blue}{\\underline{${formattedValue}}}`
            );
            
            // Store mapping for later
            placeholderMap[formattedValue] = placeholderName;
        });

        // Create container for formula
        const formulaDiv = document.createElement('div');
        formulaDiv.className = 'formula-display';
        formulaDiv.style.display = 'inline-block';

        // Render the entire formula as one LaTeX expression
        try {
            katex.render(latexString, formulaDiv, {
                throwOnError: false,
                displayMode: false,
            });
        } catch (e) {
            console.error('KaTeX rendering error:', e);
            formulaDiv.textContent = latexString;
        }

        // Now find and make draggable the numbers we marked
        // KaTeX renders \textcolor{blue}{\underline{value}} as spans with specific styling
        // We need to find elements that contain our formatted values
        makeValuesDraggable(formulaDiv, placeholderMap, values, digits);

        el.appendChild(formulaDiv);
    }

    function makeValuesDraggable(container, placeholderMap, values, digits) {
        // Strategy: Recursively find elements whose text content exactly matches our values
        // KaTeX renders \textcolor{blue}{\underline{value}} - we need to find those elements
        
        function findElementWithText(node, targetText) {
            // Check if this node's text matches
            if (node.nodeType === Node.ELEMENT_NODE) {
                const text = node.textContent.trim();
                const normalizedText = text.replace(/\s+/g, ' ');
                const normalizedTarget = targetText.replace(/\s+/g, ' ');
                
                if (normalizedText === normalizedTarget) {
                    // Check if any child also matches exactly (prefer child)
                    const children = Array.from(node.childNodes);
                    for (let child of children) {
                        if (child.nodeType === Node.ELEMENT_NODE) {
                            const childText = child.textContent.trim().replace(/\s+/g, ' ');
                            if (childText === normalizedTarget) {
                                const found = findElementWithText(child, targetText);
                                if (found) return found;
                            }
                        }
                    }
                    // No child matches exactly, so this is the element
                    return node;
                }
            }
            return null;
        }
        
        Object.keys(placeholderMap).forEach(formattedValue => {
            const placeholderName = placeholderMap[formattedValue];
            
            // Find the element containing this exact value
            const element = findElementWithText(container, formattedValue);
            
            if (element && !element.classList.contains('formula-draggable')) {
                // Check if it's already inside a draggable
                let parent = element.parentElement;
                let isInsideDraggable = false;
                while (parent && parent !== container) {
                    if (parent.classList.contains('formula-draggable')) {
                        isInsideDraggable = true;
                        break;
                    }
                    parent = parent.parentElement;
                }
                
                if (!isInsideDraggable) {
                    makeElementDraggable(element, placeholderName);
                }
            }
        });
    }

    function makeElementDraggable(element, placeholderName) {
        // Mark element as draggable
        element.classList.add('formula-draggable');
        element.dataset.placeholder = placeholderName;
        element.style.cursor = 'ew-resize';
        element.style.color = '#0066cc';
        element.style.textDecoration = 'underline';
        element.style.userSelect = 'none';
        
        // Disable pointer events on children so clicks bubble to this element
        const children = element.querySelectorAll('*');
        children.forEach(child => {
            child.style.pointerEvents = 'none';
        });
        
        element.addEventListener('mousedown', startDragging);
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
