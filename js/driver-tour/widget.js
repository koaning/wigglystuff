import { driver } from 'driver.js';

function render({ model, el }) {
  let driverObj = null;
  let startButton = null;

  // Add wrapper class for CSS variable scoping
  el.classList.add('driver-tour-wrapper');

  function initializeDriver() {
    const steps = model.get('steps');
    const showProgress = model.get('show_progress');

    if (!steps || steps.length === 0) {
      el.innerHTML = '<div class="driver-tour-empty">No tour steps defined</div>';
      return;
    }

    // Create driver instance with configuration
    driverObj = driver({
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
          element = elements[step.index] || null;
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
    startButton.onclick = () => {
      if (!driverObj) {
        initializeDriver();
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

  function initialize() {
    initializeDriver();

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
  model.on('change:steps', () => {
    if (driverObj) {
      driverObj.destroy();
      driverObj = null;
    }
    initialize();
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
