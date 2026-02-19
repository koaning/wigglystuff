import { FileDiff } from '@pierre/diffs';

const FLATTEN_EXPANDED_CSS = '[data-line-type="context-expanded"] { --diffs-line-bg: var(--diffs-bg); } [data-line-type="context-expanded"] [data-column-number] { background-color: var(--diffs-bg); }';

function render({ model, el }) {
  const container = document.createElement('div');
  container.style.width = '100%';
  el.appendChild(container);

  const instance = new FileDiff({
    theme: { dark: 'pierre-dark', light: 'pierre-light' },
    diffStyle: model.get('diff_style'),
    expandUnchanged: model.get('expand_unchanged'),
    unsafeCSS: model.get('expand_unchanged') ? FLATTEN_EXPANDED_CSS : '',
  });

  function doRender() {
    instance.setOptions({
      ...instance.options,
      diffStyle: model.get('diff_style'),
      expandUnchanged: model.get('expand_unchanged'),
      unsafeCSS: model.get('expand_unchanged') ? FLATTEN_EXPANDED_CSS : '',
    });
    instance.render({
      oldFile: { name: model.get('old_name'), contents: model.get('old_contents') },
      newFile: { name: model.get('new_name'), contents: model.get('new_contents') },
      containerWrapper: container,
    });
  }

  doRender();

  model.on('change:old_name', doRender);
  model.on('change:old_contents', doRender);
  model.on('change:new_name', doRender);
  model.on('change:new_contents', doRender);
  model.on('change:diff_style', doRender);
  model.on('change:expand_unchanged', doRender);

  return () => instance.cleanUp();
}

export default { render };
