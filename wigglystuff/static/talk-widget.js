function render({ model, el }) {
  const container = document.createElement('div');
  container.className = 'speech-container';

  const status = document.createElement('div');
  status.className = 'status-indicator';
  status.textContent = model.get('listening') ? 'Listening...' : 'Not listening';

  const display = document.createElement('div');
  display.className = 'transcript-display';
  const transcriptValue = model.get('transcript') || 'Transcript will appear here...';
  display.textContent = transcriptValue;

  const button = document.createElement('button');
  button.className = 'speech-button';
  button.textContent = model.get('listening') ? 'Stop Listening' : 'Start Listening';

  container.appendChild(status);
  container.appendChild(display);
  container.appendChild(button);
  el.appendChild(container);

  let recognition = null;

  try {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onstart = () => {
      status.textContent = 'Listening...';
      status.classList.add('active');
      button.textContent = 'Stop Listening';
      model.set('listening', true);
      model.save_changes();
    };

    recognition.onresult = (event) => {
      let finalTranscript = '';
      let interimTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript;
        } else {
          interimTranscript += transcript;
        }
      }

      const fullTranscript = finalTranscript || interimTranscript;
      display.textContent = fullTranscript || 'Transcript will appear here...';
      model.set('transcript', fullTranscript);
      model.save_changes();
    };

    recognition.onerror = (event) => {
      console.error('Speech recognition error', event.error);
      status.textContent = `Error: ${event.error}`;
      status.classList.remove('active');
      button.textContent = 'Start Listening';
      model.set('listening', false);
      model.save_changes();
    };

    recognition.onend = () => {
      status.textContent = 'Not listening';
      status.classList.remove('active');
      button.textContent = 'Start Listening';
      model.set('listening', false);
      model.save_changes();
    };
  } catch (error) {
    console.error('Speech recognition not supported', error);
    status.textContent = 'Speech recognition not supported in this browser';
    button.disabled = true;
    recognition = null;
  }

  const toggleListening = () => {
    if (!recognition) {
      return;
    }

    const isListening = model.get('listening');
    if (isListening) {
      recognition.stop();
    } else {
      recognition.start();
    }
  };

  button.addEventListener('click', toggleListening);

  model.on('change:trigger_listen', () => {
    if (model.get('trigger_listen')) {
      toggleListening();
      model.set('trigger_listen', false);
      model.save_changes();
    }
  });

  model.on('change:listening', () => {
    const isListening = model.get('listening');
    const currentlyListening = status.textContent === 'Listening...';

    if (isListening !== currentlyListening) {
      if (isListening && recognition) {
        recognition.start();
      } else if (recognition) {
        recognition.stop();
      }
    }

    button.textContent = isListening ? 'Stop Listening' : 'Start Listening';
    status.textContent = isListening ? 'Listening...' : 'Not listening';
    status.classList.toggle('active', isListening);
  });

  model.on('change:transcript', () => {
    display.textContent = model.get('transcript') || 'Transcript will appear here...';
  });
}

export default { render };
