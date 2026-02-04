function render({ model, el }) {
  el.innerHTML = '';
  const wrapper = document.createElement('div');
  wrapper.className = 'colorpicker-wrapper';

  const input = document.createElement('input');
  input.type = 'color';
  input.className = 'colorpicker-input';
  input.value = model.get('color');

  const label = document.createElement('span');
  label.className = 'colorpicker-label';

  let localUpdate = false;

  const syncFromModel = () => {
    const color = model.get('color') || '#000000';
    input.value = color;
    label.textContent = color;
    const showLabel = model.get('show_label');
    label.style.display = showLabel === false ? 'none' : '';

    if (!localUpdate) {
      // Echo backend-driven updates so marimo can react to programmatic changes.
      model.save_changes();
    }
    localUpdate = false;
  };

  input.addEventListener('input', () => {
    localUpdate = true;
    model.set('color', input.value);
    model.save_changes();
  });

  model.on('change:color', syncFromModel);
  model.on('change:show_label', syncFromModel);

  wrapper.appendChild(input);
  wrapper.appendChild(label);
  el.appendChild(wrapper);

  syncFromModel();
}

export default { render };
