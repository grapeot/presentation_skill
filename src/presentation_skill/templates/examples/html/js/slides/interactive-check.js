let button = null;
let output = null;

export const html = `
  <h2>Use a module only when a slide has a lifecycle</h2>
  <div class="interactive-panel">
    <p id="check-output">The listener is installed only while this slide is active.</p>
    <button id="check-button" type="button">Run check</button>
  </div>
  <p class="thesis-line">Static slides stay in the deck registry. Interactive slides initialize and clean up explicitly.</p>
  <aside class="notes">Move timers, event listeners, charts, and WebGL into modules with explicit cleanup. Do not impose that ceremony on static slides.</aside>
`;

function runCheck() {
  output.textContent = 'Lifecycle check passed.';
}

export function initialize() {
  button = document.getElementById('check-button');
  output = document.getElementById('check-output');
  button?.addEventListener('click', runCheck);
}

export function cleanup() {
  button?.removeEventListener('click', runCheck);
  button = null;
  output = null;
}
