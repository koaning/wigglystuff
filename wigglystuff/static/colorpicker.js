function render({model, el}) {
  const ip = document.createElement('input');
  ip.type = 'color';
  ip.value = model.get('color');

  ip.addEventListener('input', () => {
    model.set('color', ip.value);
    model.save_changes();
  });

  model.on('change:color', () => {
    ip.value = model.get('color');
  });

  el.appendChild(ip);
}

export default { render };
