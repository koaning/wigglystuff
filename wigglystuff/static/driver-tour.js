// Import Driver.js from CDN using ESM
async function loadDriverJS() {
  // Load CSS
  if (!document.querySelector('link[href*="driver.js"]')) {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'https://cdn.jsdelivr.net/npm/driver.js@1.3.1/dist/driver.css';
    document.head.appendChild(link);
  }

  // Use dynamic import for ESM version
  const module = await import('https://cdn.jsdelivr.net/npm/driver.js@1.3.1/+esm');
  return module.driver;
}

function render({ model, el }) {
  let driverObj = null;
  let startButton = null;

  async function initializeDriver() {
    const driverConstructor = await loadDriverJS();
    const steps = model.get('steps');
    const showProgress = model.get('show_progress');

    if (!steps || steps.length === 0) {
      el.innerHTML = '<div class="driver-tour-empty">No tour steps defined</div>';
      return;
    }

    // Create driver instance with configuration
    driverObj = driverConstructor({
      showProgress: showProgress,
      allowClose: true,
      showButtons: ['next', 'previous', 'close'],
      onDestroyStarted: () => {
        if (driverObj) {
          driverObj.destroy();
          model.set('active', false);
          model.set('current_step', 0);
          model.save_changes();
          renderButton();
        }
      },
      onNextClick: () => {
        driverObj.moveNext();
        model.set('current_step', driverObj.getActiveIndex());
        model.save_changes();
      },
      onPrevClick: () => {
        driverObj.movePrevious();
        model.set('current_step', driverObj.getActiveIndex());
        model.save_changes();
      },
      steps: steps.map(step => {
        // Handle indexed selection if index is provided
        let element = step.element || null;
        if (element && step.index !== undefined) {
          const elements = document.querySelectorAll(element);
          console.log(`Selector: ${element}, Found: ${elements.length}, Index: ${step.index}`);
          element = elements[step.index] || null;
          console.log('Selected element:', element);
        }

        return {
          element: element,
          popover: {
            title: step.popover?.title || '',
            description: step.popover?.description || '',
            side: step.popover?.position || 'bottom',
            align: step.popover?.align || 'start',
          }
        };
      })
    });

    return driverObj;
  }

  function renderButton() {
    el.innerHTML = '';
    startButton = document.createElement('button');
    startButton.className = 'driver-tour-start-button';
    startButton.textContent = 'Start Tour';
    startButton.onclick = async () => {
      if (!driverObj) {
        await initializeDriver();
      }
      if (driverObj) {
        driverObj.drive();
        model.set('active', true);
        model.save_changes();
        el.innerHTML = '';
      }
    };
    el.appendChild(startButton);
  }

  async function initialize() {
    await initializeDriver();

    if (model.get('auto_start')) {
      if (driverObj) {
        driverObj.drive();
        model.set('active', true);
        model.save_changes();
      }
    } else {
      renderButton();
    }
  }

  // Handle step changes from Python
  model.on('change:steps', async () => {
    if (driverObj) {
      driverObj.destroy();
      driverObj = null;
    }
    await initialize();
  });

  // Handle auto_start changes
  model.on('change:auto_start', () => {
    if (model.get('auto_start') && !model.get('active')) {
      if (startButton) {
        startButton.click();
      }
    }
  });

  // Initialize on load
  initialize();
}

export default { render };
