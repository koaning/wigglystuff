function render({model, el}){
    const config = {
        rows: model.get("rows"),
        cols: model.get("cols"),
        minValue: model.get("min_value"),
        maxValue: model.get("max_value"),
        isTriangular: model.get("triangular"),
        stepSize: model.get("step"),
        pixelsPerStep: 2
    };

    let matrix = model.get("matrix");

    const container = document.createElement('div');
    container.classList.add("matrixElem");
    el.appendChild(container);


    function renderMatrix() {
        container.innerHTML = '';
        
        matrix.forEach((row, rowIndex) => {
            const rowElement = document.createElement('div');
            rowElement.className = 'matrix-row';
            row.forEach((value, colIndex) => {
                const element = document.createElement('span');
                element.className = 'matrix-element';
                element.textContent = value.toFixed(1);
                element.dataset.row = rowIndex;
                element.dataset.col = colIndex;
                element.addEventListener('mousedown', startDragging);
                rowElement.appendChild(element);
                matrix[rowIndex][colIndex] = parseFloat(value.toFixed(1));
            });
            container.appendChild(rowElement);
        });
    }

    function startDragging(e) {
        e.preventDefault();
        const element = e.target;
        const startX = e.clientX;
        const startValue = parseFloat(element.textContent);
        const row = parseInt(element.dataset.row);
        const col = parseInt(element.dataset.col);

        function onMouseMove(e) {
            const deltaX = e.clientX - startX;
            const steps = Math.floor(deltaX / config.pixelsPerStep);
            const newValue = Math.max(config.minValue, Math.min(config.maxValue, startValue + steps * config.stepSize));
            updateMatrixValue(row, col, newValue);
            renderMatrix();
        }

        function onMouseUp() {
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
        }

        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
    }

    function updateMatrixValue(row, col, value) {
        matrix[row][col] = parseFloat(value.toFixed(1));
        if (config.isTriangular && col < config.rows && row < config.cols) {
            matrix[col][row] = parseFloat(value.toFixed(1));
        }
        model.set("matrix", matrix);
        model.save_changes();
    }

    renderMatrix();
}

export default { render };
