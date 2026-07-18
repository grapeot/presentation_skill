export const slides = {
  opening: `
    <div class="hero-slide">
      <div class="eyebrow">Reveal mode reference</div>
      <h1>Precision in the DOM.<br><span>Visual leverage from generated assets.</span></h1>
      <p>Use HTML for exact copy, layout, links, and interaction. Use image generation where a local visual explains faster than another paragraph.</p>
    </div>
    <aside class="notes">This reference deck shows the intended Reveal mode: browser-native composition with optional generated assets.</aside>
  `,

  'capability-compare': `
    <h2>Rendering and memory are different jobs</h2>
    <div class="two-column">
      <article class="comparison-card">
        <div class="card-label">Compute</div>
        <div class="card-visual"><img src="imgs/cpu-blueprint.svg" alt="Flat line icon of a CPU"></div>
        <h3>Fast execution</h3>
        <p>The model handles the current task, then the session ends.</p>
      </article>
      <article class="comparison-card">
        <div class="card-label">Context</div>
        <div class="card-visual text-visual" aria-hidden="true">FILES</div>
        <h3>Durable knowledge</h3>
        <p>The workspace keeps facts, methods, and decisions available for later runs.</p>
      </article>
    </div>
    <p class="thesis-line">The generated icon supports the distinction. The DOM still owns every exact word.</p>
    <aside class="notes">The CPU fixture is intentionally local and textless. It could come from any image-generation provider and be normalized with prepare-asset.</aside>
  `,

  'asset-pipeline': `
    <h2>Generated visuals become reliable through a deterministic boundary</h2>
    <div class="process-row">
      <div><b>1</b><strong>Generate</strong><span>One semantic icon</span></div>
      <i>→</i>
      <div><b>2</b><strong>Normalize</strong><span>Alpha, tint, crop</span></div>
      <i>→</i>
      <div><b>3</b><strong>Compose</strong><span>Stable DOM container</span></div>
      <i>→</i>
      <div><b>4</b><strong>Verify</strong><span>Two surfaces, full deck</span></div>
    </div>
    <p class="thesis-line">Probabilistic pixels enter through a deterministic interface.</p>
    <aside class="notes">The browser owns geometry and text. The generated asset has one bounded visual role.</aside>
  `,
};
