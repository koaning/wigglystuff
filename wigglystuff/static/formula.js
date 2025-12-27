function render({model, el}) {
    // Check if KaTeX is available (it might be in marimo/Jupyter environments)
    const katexAvailable = typeof window.katex !== 'undefined';
    
    if (!katexAvailable) {
        // Try to use KaTeX from common locations
        const katexFromWindow = window.katex || 
                                (window.require && window.require('katex')) ||
                                (window.define && window.define.amd);
        
        if (!katexFromWindow) {
            console.warn('KaTeX not available. Formula widget requires KaTeX for LaTeX rendering.');
            el.innerHTML = '<span style="color: red;">KaTeX not available. Please ensure KaTeX is loaded.</span>';
            return;
        }
    }

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

        // Build LaTeX string with values substituted
        let latexString = formula;
        const placeholderMap = {}; // Maps formatted value -> placeholder name
        
        Object.keys(values).forEach(placeholderName => {
            const value = values[placeholderName];
            const decimalPlaces = digits[placeholderName] || 1;
            const formattedValue = value.toFixed(decimalPlaces);
            
            // Replace placeholder with formatted value
            const placeholderRegex = new RegExp(`\\{${placeholderName}\\}`, 'g');
            latexString = latexString.replace(placeholderRegex, formattedValue);
            
            // Store mapping for finding in DOM later
            placeholderMap[formattedValue] = placeholderName;
        });

        // Create container for formula
        const formulaDiv = document.createElement('div');
        formulaDiv.className = 'formula-display';
        formulaDiv.style.display = 'inline-block';

        // Render the entire formula as one LaTeX expression
        try {
            window.katex.render(latexString, formulaDiv, {
                throwOnError: false,
                displayMode: false,
            });
        } catch (e) {
            console.error('KaTeX rendering error:', e);
            formulaDiv.textContent = latexString;
            el.appendChild(formulaDiv);
            return;
        }

        // Now find and wrap the number nodes to make them draggable
        // Use a small delay to ensure KaTeX has finished rendering
        setTimeout(() => {
            makeValuesDraggable(formulaDiv, placeholderMap, values, digits);
        }, 0);

        el.appendChild(formulaDiv);
    }

    function makeValuesDraggable(container, placeholderMap, values, digits) {
        // Strategy: Find elements whose text content exactly matches our formatted values
        // This works for exponents, fractions, vectors, and matrices because KaTeX
        // renders numbers as text nodes or simple elements that we can find
        
        Object.keys(placeholderMap).forEach(formattedValue => {
            const placeholderName = placeholderMap[formattedValue];
            const searchText = formattedValue.trim();
            const normalizedSearch = searchText.replace(/\s+/g, '');
            
            // Get all elements and text nodes in the rendered formula
            const allNodes = [];
            const walker = document.createTreeWalker(
                container,
                NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT,
                null,
                false
            );
            
            let node;
            while (node = walker.nextNode()) {
                allNodes.push(node);
            }
            
            // Find candidates: nodes that contain exactly our value
            // This will find numbers in exponents (superscripts), fractions, vectors, etc.
            const candidates = [];
            
            for (const node of allNodes) {
                if (node.classList && node.classList.contains('formula-draggable')) continue;
                
                let text;
                if (node.nodeType === Node.TEXT_NODE) {
                    text = node.textContent.trim();
                } else if (node.nodeType === Node.ELEMENT_NODE) {
                    // For elements, get their text content
                    // This works for numbers in superscripts, subscripts, fractions, etc.
                    text = node.textContent.trim();
                } else {
                    continue;
                }
                
                const normalizedText = text.replace(/\s+/g, '');
                
                // Check for exact match (handles numbers in any LaTeX structure)
                if (text === searchText || normalizedText === normalizedSearch) {
                    // Check if already inside a draggable
                    let parent = node.parentElement || node.parentNode;
                    let isInsideDraggable = false;
                    let depth = 0;
                    
                    while (parent && parent !== container) {
                        depth++;
                        if (parent.classList && parent.classList.contains('formula-draggable')) {
                            isInsideDraggable = true;
                            break;
                        }
                        parent = parent.parentElement || parent.parentNode;
                    }
                    
                    if (!isInsideDraggable) {
                        candidates.push({node, depth, text, isTextNode: node.nodeType === Node.TEXT_NODE});
                    }
                }
            }
            
            // Find the best candidate (prefer text nodes, then innermost elements)
            if (candidates.length > 0) {
                // Sort: text nodes first, then by depth (deeper = more specific)
                candidates.sort((a, b) => {
                    if (a.isTextNode !== b.isTextNode) {
                        return a.isTextNode ? -1 : 1; // Text nodes first
                    }
                    return b.depth - a.depth; // Deeper first
                });
                
                const bestCandidate = candidates[0];
                const bestNode = bestCandidate.node;
                
                // For element nodes, check if a direct text child matches (prefer text node)
                if (bestNode.nodeType === Node.ELEMENT_NODE) {
                    const children = Array.from(bestNode.childNodes);
                    const textChild = children.find(child => {
                        if (child.nodeType === Node.TEXT_NODE) {
                            const childText = child.textContent.trim().replace(/\s+/g, '');
                            return childText === normalizedSearch;
                        }
                        return false;
                    });
                    
                    if (textChild) {
                        wrapTextNode(textChild, placeholderName, formattedValue);
                        return; // Found and wrapped, move to next placeholder
                    }
                }
                
                // Wrap the best candidate
                if (bestNode.nodeType === Node.TEXT_NODE) {
                    wrapTextNode(bestNode, placeholderName, formattedValue);
                } else {
                    wrapElement(bestNode, placeholderName);
                }
            }
        });
    }

    function wrapTextNode(textNode, placeholderName, formattedValue) {
        // Create wrapper span
        const wrapper = document.createElement('span');
        wrapper.className = 'formula-draggable';
        wrapper.dataset.placeholder = placeholderName;
        
        // Copy computed styles from parent to preserve KaTeX styling
        // This is important for superscripts, subscripts, fractions, etc.
        const parent = textNode.parentElement;
        if (parent) {
            const computedStyle = window.getComputedStyle(parent);
            // Copy all relevant font properties to match KaTeX rendering
            wrapper.style.fontFamily = computedStyle.fontFamily;
            wrapper.style.fontSize = computedStyle.fontSize;
            wrapper.style.fontStyle = computedStyle.fontStyle;
            wrapper.style.fontWeight = computedStyle.fontWeight;
            wrapper.style.verticalAlign = computedStyle.verticalAlign;
            wrapper.style.lineHeight = computedStyle.lineHeight;
        }
        
        wrapper.style.cursor = 'ew-resize';
        wrapper.style.color = '#0066cc';
        wrapper.style.textDecoration = 'underline';
        wrapper.style.userSelect = 'none';
        wrapper.style.display = 'inline-block';
        wrapper.style.position = 'relative';
        
        // Replace text node with wrapper
        textNode.parentNode.replaceChild(wrapper, textNode);
        wrapper.textContent = formattedValue;
        wrapper.addEventListener('mousedown', startDragging);
    }

    function wrapElement(element, placeholderName) {
        // Mark element as draggable, preserving all KaTeX styling
        // This preserves styling for numbers in complex structures
        element.classList.add('formula-draggable');
        element.dataset.placeholder = placeholderName;
        
        // Preserve existing styles (important for superscripts/subscripts)
        const computedStyle = window.getComputedStyle(element);
        element.style.cursor = 'ew-resize';
        element.style.color = '#0066cc';
        element.style.textDecoration = 'underline';
        element.style.userSelect = 'none';
        // Don't override font-size, vertical-align, etc. - preserve KaTeX's styling
        
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
