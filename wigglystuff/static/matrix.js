function render({model, el}){
    const config = {
        rows: model.get("rows"),
        cols: model.get("cols"),
        minValue: model.get("min_value"),
        maxValue: model.get("max_value"),
        isTriangular: model.get("triangular")
    };
    console.log(config);
    
    let matrix = Array(config.rows).fill().map(() => Array(config.cols).fill(0));
    
    const container = document.createElement('div');
    container.classList.add("matrixElem")
    el.appendChild(container)
    
    function renderMatrix() {
        container.innerHTML = '';
        matrix.forEach((row, i) => {
            const rowElement = document.createElement('div');
            rowElement.className = 'matrix-row';
            row.forEach((value, j) => {
                const element = document.createElement('span');
                element.className = 'matrix-element';
                element.textContent = value;
                element.dataset.row = i;
                element.dataset.col = j;
                element.addEventListener('mousedown', startDragging);
                rowElement.appendChild(element);
            });
            container.appendChild(rowElement);
        });
    }
    
    function startDragging(e) {
        e.preventDefault();
        const element = e.target;
        const startX = e.clientX;
        const startValue = parseInt(element.textContent);
        const row = parseInt(element.dataset.row);
        const col = parseInt(element.dataset.col);
    
        function onMouseMove(e) {
            const deltaX = e.clientX - startX;
            const newValue = Math.max(config.minValue, Math.min(config.maxValue, startValue + Math.floor(deltaX / 5)));
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
        matrix[row][col] = value;
        if (config.isTriangular && row !== col) {
            matrix[col][row] = value;
        }
    }
    
    renderMatrix();    
}

export default { render };
