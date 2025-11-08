function render({model, el}){
    const config = {
        rows: model.get("rows"),
        cols: model.get("cols"),
        minValue: model.get("min_value"),
        maxValue: model.get("max_value"),
        isMirrored: model.get("mirror"),
        stepSize: model.get("step"),
        digits: model.get("digits"),
        pixelsPerStep: 2,
        rowNames: model.get("row_names"),
        colNames: model.get("col_names"),
        isStatic: model.get("static"),
        flexibleColumns: model.get("flexible_cols")
    };
    
    let matrix = JSON.parse(JSON.stringify(model.get("matrix"))); // Deep copy

    const wrapper = document.createElement('div');
    wrapper.classList.add("matrix-wrapper");
    el.appendChild(wrapper);

    function renderMatrix() {
        wrapper.innerHTML = '';
        
        // Create main grid container
        const gridContainer = document.createElement('div');
        gridContainer.className = 'matrix-grid';
        if (config.flexibleColumns) {
            gridContainer.classList.add('flexible-columns');
        }
        
        // First column for row labels (if they exist)
        if (config.rowNames.length > 0) {
            const rowLabelColumn = document.createElement('div');
            rowLabelColumn.className = 'matrix-column matrix-label-column';
            
            // Empty corner cell if we have column names
            if (config.colNames.length > 0) {
                const corner = document.createElement('div');
                corner.className = 'matrix-cell matrix-corner-cell';
                rowLabelColumn.appendChild(corner);
            }
            
            // Row labels
            config.rowNames.forEach(name => {
                const cell = document.createElement('div');
                cell.className = 'matrix-cell matrix-row-label';
                cell.textContent = name;
                rowLabelColumn.appendChild(cell);
            });
            
            gridContainer.appendChild(rowLabelColumn);
        }
        
        // Create matrix container that will hold all data columns
        const matrixWrapper = document.createElement('div');
        matrixWrapper.className = 'matrix-data-wrapper';
        
        // Create columns for each matrix column
        for (let colIndex = 0; colIndex < config.cols; colIndex++) {
            const column = document.createElement('div');
            column.className = 'matrix-column matrix-data-column';
            
            // Column header if exists
            if (config.colNames.length > 0) {
                const header = document.createElement('div');
                header.className = 'matrix-cell matrix-col-label';
                header.textContent = config.colNames[colIndex] || '';
                column.appendChild(header);
            }
            
            // Matrix values
            matrix.forEach((row, rowIndex) => {
                const cell = document.createElement('div');
                cell.className = 'matrix-cell matrix-element';
                if (config.isStatic) {
                    cell.classList.add('matrix-element-static');
                }
                cell.textContent = row[colIndex].toFixed(config.digits);
                cell.dataset.row = rowIndex;
                cell.dataset.col = colIndex;
                if (!config.isStatic) {
                    cell.addEventListener('mousedown', startDragging);
                }
                column.appendChild(cell);
            });
            
            matrixWrapper.appendChild(column);
        }
        
        gridContainer.appendChild(matrixWrapper);
        wrapper.appendChild(gridContainer);

        updateModel();
    };

    function updateModel() {
        model.set("matrix", JSON.parse(JSON.stringify(matrix))); // Deep copy
        model.save_changes();
    };

    let updateTimeout;
    function debouncedUpdateModel() {
        clearTimeout(updateTimeout);
        updateTimeout = setTimeout(updateModel, 100); // Debounce for 100ms
    };

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
            debouncedUpdateModel();
        }

        function onMouseUp() {
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
            updateModel(); // Ensure final state is updated
        }

        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
    };

    function updateMatrixValue(row, col, value) {
        matrix[row][col] = parseFloat(value.toFixed(config.digits));
        if (config.isMirrored && (col < config.rows) && (row < config.cols)) {
            matrix[col][row] = parseFloat(value.toFixed(config.digits));
        }
    };

    renderMatrix();
}

export default { render };