/* HTML canvas engine.
   Reveal owns navigation, fragments, notes and speaker view (press S).
   The picture is one world div: frames are laid out on a long sheet in slide order and a camera moves between them.
   Every element's state is a pure function of (slide, step), so back, jump and reload are exact.

   Markup vocabulary (see tools/build_index.py):
     data-in="slide.step" [data-out="slide.step"]  present while in <= position < out ("end.0" = never retires)
     data-state="cls@slide.step[-slide.step]"      add class cls inside that range
     data-flap="a b"                               split-flap cell: come / cur / gone
     data-count="slide.step" data-from data-to     number rolls to its value when stepping forward
     data-bar / data-follow / data-yearlabel       SVG bar height, label y, label text per state
     data-slot="slide.slot"                        filled from window.COPY (the writer's copy)
     data-no-nav                                   touches inside never navigate (a, button and form fields are skipped already)
     data-goto="slide.step"                        a jump chip (a button): jumps there; R returns to the exact slide and step
   Slide table extras (js/deck.js opts): { appendix: true } = reached only through a jump chip; plain "next" never
   walks from the last main slide into it. Appendix slides are numbered A1, A2 ... after the main deck.
   Speaker notes (copy.md "### notes"): a paragraph "[click]" marks a build step; a paragraph wholly in [brackets]
   is a stage direction, shown in a different style and not read aloud.
   Optional per-slide hooks for live content (charts, WebGL, video):
     window.DECK_HOOKS = { slideId: { enter(step) {}, leave() {} } } */
(function () {
  const W = 1920, H = 1080;
  const stage = document.getElementById("stage");
  const world = document.getElementById("world");
  const DECK = window.DECK, COPY = window.COPY || {};
  /* look frames up inside the world: if a Reveal section ever carries the same id (for readable hash URLs),
     document.getElementById would return the section, and the navigator would lay out nothing */
  const frameEl = f => world.querySelector("#" + CSS.escape(f));

  /* ---------- fit the 1920x1080 stage into the window ---------- */
  function fit() {
    const s = Math.min(innerWidth / W, innerHeight / H);
    stage.style.transform = `translate(-50%, -50%) scale(${s})`;
  }
  fit(); addEventListener("resize", fit);

  /* ---------- copy slots ---------- */
  const get = (o, path) => path.split(".").reduce((a, k) => (a == null ? a : a[k]), o);
  document.querySelectorAll("[data-slot]").forEach(el => {
    const v = get(COPY, el.dataset.slot);
    if (typeof v === "string" && v.trim()) el.textContent = v.trim();
    else { el.textContent = "[" + el.dataset.slot + "]"; el.classList.add("missing"); }
  });

  /* ---------- typewriter: split into letters, keep words unbreakable ---------- */
  document.querySelectorAll(".type").forEach(el => {
    const text = el.textContent; el.textContent = ""; let i = 0;
    text.split(/(\s+)/).forEach(w => {
      if (!w) return;
      if (/^\s+$/.test(w)) { el.appendChild(document.createTextNode(" ")); return; }
      const word = document.createElement("span"); word.style.whiteSpace = "nowrap";
      for (const c of w) { const s = document.createElement("span"); s.className = "ch"; s.textContent = c; s.style.setProperty("--i", i++); word.appendChild(s); }
      el.appendChild(word);
    });
  });

  /* ---------- codes: "rag_split.2" -> slide index * 100 + step ("end" = after the last slide) ---------- */
  const IDX = {}; DECK.forEach((s, i) => { IDX[s.id] = i; });
  const code = s => {
    const [id, st] = s.trim().split(".");
    if (id === "end") return 1e9;
    if (!(id in IDX)) { console.warn("unknown slide id", s); return NaN; }
    return IDX[id] * 100 + (+st || 0);
  };
  const slideNo = i => i;
  const MAIN = DECK.filter(s => !s.appendix).length;
  const NO = {}; { let n = 0, a = 0; DECK.forEach(s => { NO[s.id] = s.appendix ? "A" + (++a) : String(++n).padStart(2, "0"); }); }
  const esc = t => String(t).replace(/&/g, "&amp;").replace(/</g, "&lt;");

  /* ---------- lay frames out on the sheet in slide order ---------- */
  const FRAME_POS = {}; let k = 0;
  DECK.forEach(s => {
    const f = s.frame || s.id;
    if (f in FRAME_POS) return;
    const el = frameEl(f);
    if (!el) { console.warn("missing frame", f); return; }
    FRAME_POS[f] = [k * 2200, 0]; el.style.left = (k * 2200) + "px"; el.style.top = "0px"; k++;
  });
  world.style.width = (k * 2200) + "px";
  const camFor = (s, step) => {
    const [fx, fy] = FRAME_POS[s.frame || s.id];
    let c = s.cam || [0, 0, 1];
    if (Array.isArray(c[0])) c = c[Math.min(step, c.length - 1)];
    return [fx + 960 + c[0], fy + 540 + c[1], c[2]];
  };

  /* ---------- build Reveal sections ---------- */
  const slidesEl = document.querySelector(".reveal .slides");
  DECK.forEach((s, i) => {
    const sec = document.createElement("section");
    sec.dataset.idx = i;
    for (let k = 1; k < s.steps; k++) { const f = document.createElement("span"); f.className = "fragment"; sec.appendChild(f); }
    const notes = document.createElement("aside"); notes.className = "notes";
    const n = (COPY[s.id] && COPY[s.id].notes) || "";
    let click = 0;
    notes.innerHTML = n.split(/\n\s*\n/).map(p => p.trim()).filter(Boolean).map(p =>
      /^`?\[click\]`?$/i.test(p) ? `<p><b>▶ click ${++click}</b></p>`
      : /^`?\[[^\]]+\]`?$/.test(p) ? `<p style="color:#7a5a2b;background:#f3ead8;border-left:4px solid #b8863b;padding:6px 10px;border-radius:4px"><i>${esc(p.replace(/^`|`$/g, ""))}</i></p>`
      : `<p>${esc(p)}</p>`).join("");
    if (click && click !== s.steps - 1) console.error(`notes for ${s.id} have ${click} click cues, the slide has ${s.steps - 1} clicks`);
    sec.appendChild(notes);
    slidesEl.appendChild(sec);
  });

  /* ---------- camera ---------- */
  let cam = null, camAnim = null;
  const setCam = c => { world.style.transform = `translate(${W / 2 - c[0] * c[2]}px, ${H / 2 - c[1] * c[2]}px) scale(${c[2]})`; cam = c.slice(); };
  const ease = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  function flyTo(t, animate, fixedDur) {
    if (camAnim) cancelAnimationFrame(camAnim);
    if (!cam || !animate) { setCam(t); world.style.willChange = "auto"; return; }
    const a = cam.slice(), dx = t[0] - a[0], dy = t[1] - a[1];
    const dist = Math.hypot(dx, dy) * Math.min(a[2], t[2]);
    if (dist < 1 && Math.abs(t[2] - a[2]) < 1e-3) { setCam(t); return; }
    const far = !fixedDur && dist > 2600;              // leaving a set: lift the camera
    const dur = fixedDur || Math.min(2200, 950 + dist * 0.22);
    const zDip = far ? Math.min(a[2], t[2]) * 0.62 : null;
    const t0 = performance.now();
    const la = Math.log(a[2]), lb = Math.log(t[2]);
    const step = now => {
      const k = Math.min(1, (now - t0) / dur), e = ease(k);
      let lz = la + (lb - la) * e;
      if (far) lz += (Math.log(zDip) - Math.min(la, lb)) * Math.sin(Math.PI * k);   // arc out and back in
      setCam([a[0] + dx * e, a[1] + dy * e, Math.exp(lz)]);
      if (k < 1) camAnim = requestAnimationFrame(step); else { camAnim = null; world.style.willChange = "auto"; }   // settle: re-raster crisp at the new zoom
    };
    world.style.willChange = "transform";                    // a compositor layer only while flying
    camAnim = requestAnimationFrame(step);
  }

  /* ---------- counters ---------- */
  const fmt = (v, el) => {
    const dec = +(el.dataset.dec || 0), suf = el.dataset.suffix || "";
    return (dec ? v.toFixed(dec) : Math.round(v).toLocaleString("en-US")) + suf;
  };
  function roll(el, from, to, animate) {
    if (el._raf) cancelAnimationFrame(el._raf);
    if (!animate) { el.textContent = fmt(to, el); return; }
    const t0 = performance.now(), dur = 1300;
    const tick = now => { const k = Math.min(1, (now - t0) / dur), e = 1 - Math.pow(1 - k, 3); el.textContent = fmt(from + (to - from) * e, el); if (k < 1) el._raf = requestAnimationFrame(tick); };
    el._raf = requestAnimationFrame(tick);
  }

  /* ---------- apply state for a global position ---------- */
  let prev = -1;
  /* each frame's final step, for the navigator's overview (every frame shown complete) */
  const FRAME_FINAL = {};
  DECK.forEach((s, i) => { const f = s.frame || s.id; FRAME_FINAL[f] = Math.max(FRAME_FINAL[f] ?? -1, i * 100 + s.steps - 1); });
  const frameCur = el => { if (el._fc === undefined) { const fr = el.closest(".frame"); el._fc = fr && fr.id in FRAME_FINAL ? FRAME_FINAL[fr.id] : null; } return el._fc; };
  function apply(globalCur, animate, perFrame) {
    const at = el => (perFrame && frameCur(el) != null) ? frameCur(el) : globalCur;
    document.querySelectorAll("[data-in]").forEach(el => {
      const cur = at(el), a = code(el.dataset.in), b = el.dataset.out ? code(el.dataset.out) : Infinity;
      el.classList.toggle("on", cur >= a && cur < b);
    });
    document.querySelectorAll("[data-state]").forEach(el => {
      const cur = at(el);
      el.dataset.state.split(/\s+/).filter(Boolean).forEach(tok => {
        const [cls, rng] = tok.split("@"); const [a, b] = rng.split("-");
        const lo = code(a), hi = b ? code(b) : Infinity;
        if (!isNaN(lo)) el.classList.toggle(cls, cur >= lo && cur < hi);
      });
    });
    document.querySelectorAll("[data-flap]").forEach(el => {
      const cur = at(el), [a, b] = el.dataset.flap.split(/\s+/).map(code);
      el.classList.toggle("come", cur < a); el.classList.toggle("cur", cur >= a && cur < b); el.classList.toggle("gone", cur >= b);
    });
    document.querySelectorAll("[data-count]").forEach(el => {
      const cur = at(el), c = code(el.dataset.count), from = +el.dataset.from, to = +el.dataset.to;
      const want = cur >= c ? to : from;
      const crossing = animate && !perFrame && prev < c && cur >= c && cur - prev <= 1;
      if (el._v !== want) { roll(el, crossing ? from : want, want, crossing); el._v = want; }
    });
    document.querySelectorAll("[data-bar]").forEach(el => {
      const cur = at(el), c = code(el.dataset.bar), h = cur >= c ? +el.dataset.h1 : +el.dataset.h0;
      el.setAttribute("height", h); el.setAttribute("y", (+el.dataset.base || 480) - h);
    });
    document.querySelectorAll("[data-follow]").forEach(el => {
      const cur = at(el), c = code(el.dataset.follow); el.setAttribute("y", cur >= c ? el.dataset.y1 : el.dataset.y0);
    });
    document.querySelectorAll("[data-yearlabel]").forEach(el => {
      const cur = at(el), c = code(el.dataset.yearlabel); el.textContent = cur >= c ? el.dataset.t1 : el.dataset.t0;
    });
    if (!perFrame) prev = globalCur;
  }

  /* ---------- sync with Reveal ---------- */
  function position() {
    const ix = Reveal.getIndices(); const i = ix.h || 0;
    const step = (ix.f == null || ix.f < 0) ? 0 : ix.f + 1;
    return { i, step, cur: slideNo(i) * 100 + step };
  }
  const HOOKS = window.DECK_HOOKS || {}; let activeSlide = null;
  function update(animate) {
    const { i, step, cur } = position(); const s = DECK[i];
    if (activeSlide !== s.id) { if (activeSlide && HOOKS[activeSlide] && HOOKS[activeSlide].leave) HOOKS[activeSlide].leave(); activeSlide = s.id; }
    if (HOOKS[s.id] && HOOKS[s.id].enter) HOOKS[s.id].enter(step);
    apply(cur, animate);
    flyTo(camFor(s, step), animate);
    const part = document.getElementById("part"), folio = document.getElementById("folio");
    if (part) part.textContent = s.part || "";
    if (folio) folio.textContent = NO[s.id] + " / " + String(MAIN).padStart(2, "0");
    const prog = document.getElementById("progress");
    if (prog) prog.style.width = (Math.min(1, (s.appendix ? MAIN : i + (step + 1) / s.steps) / MAIN) * 1728) + "px";
  }


  /* ---------- jumps: any [data-goto="slide.step"]; R returns to where the last jump left. Plain "next" never
     walks from the last main slide into the appendix. ---------- */
  const back = []; let jumping = false, lastIdx = 0;
  function goto(target) {
    const [id, st] = target.split("."); if (!(id in IDX)) { console.warn("unknown jump target", target); return; }
    const p = position(); back.push([p.i, p.step]);
    jumping = true; Reveal.slide(IDX[id], 0, (+st || 0) - 1); jumping = false;
  }
  document.addEventListener("click", e => {
    const el = e.target.closest && e.target.closest("[data-goto]");
    if (!el || el.disabled || document.body.classList.contains("nav-open")) return;
    e.preventDefault(); e.stopPropagation(); goto(el.dataset.goto);
    /* never leave focus on a chip: a focused button turns the presenter's next Space into a second jump */
    if (document.activeElement && document.activeElement !== document.body) document.activeElement.blur();
  });
  document.addEventListener("mousedown", e => { if (e.target.closest && e.target.closest("[data-goto]")) e.preventDefault(); });
  addEventListener("keydown", e => {
    if (e.metaKey || e.ctrlKey || e.altKey || e.repeat || document.body.classList.contains("nav-open")) return;
    /* R, not B: B and "." are Reveal's blackout keys, which also freeze navigation until pressed again */
    if ((e.key === "r" || e.key === "R") && back.length) {
      e.preventDefault(); const [i, st] = back.pop(); jumping = true; Reveal.slide(i, 0, st - 1); jumping = false;
    }
  });
  Reveal.on("slidechanged", () => {
    const i = position().i, s = DECK[i];
    if (s && s.appendix && !jumping && !DECK[lastIdx].appendix) { Reveal.slide(lastIdx, 0, DECK[lastIdx].steps - 2); return; }
    lastIdx = i;
  });

  /* ---------- navigator: M (or the grid button) pulls the camera back over every frame, laid out in a grid and
     shown complete; pick one with the mouse, the arrows or by typing its number, Enter to fly in, Esc to go back ---------- */
  const FRAMES = []; { const seen = {}; DECK.forEach((s, i) => { const f = s.frame || s.id; if (!(f in seen)) { seen[f] = FRAMES.length; FRAMES.push({ f, i, el: frameEl(f) }); } }); }
  const COLS = Math.max(1, Math.round(Math.sqrt(FRAMES.length * 1.5)));
  const CELL_W = 2200, CELL_H = 1400;
  const titleOf = fr => { const d = fr.el && fr.el.querySelector(".display"); const t = (d ? d.textContent : fr.f).replace(/\s+/g, " ").trim(); return t.length > 90 ? t.slice(0, 88) + "…" : t; };
  let nav = null;
  const hud = document.createElement("div"); hud.id = "navhud"; stage.appendChild(hud);
  const navBtn = document.createElement("button"); navBtn.id = "navbtn"; navBtn.type = "button"; navBtn.title = "All slides (M)"; navBtn.setAttribute("aria-label", "All slides");
  navBtn.innerHTML = '<svg viewBox="0 0 24 24" width="22" height="22"><g fill="currentColor"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></g></svg>';
  navBtn.addEventListener("click", e => { e.stopPropagation(); nav ? closeNav(nav.sel) : openNav(); });
  document.body.appendChild(navBtn);
  const gridPos = k => [(k % COLS) * CELL_W, Math.floor(k / COLS) * CELL_H];
  function select(k) {
    if (!nav) return; k = Math.max(0, Math.min(FRAMES.length - 1, k)); nav.sel = k;
    FRAMES.forEach((fr, j) => fr.el && fr.el.classList.toggle("nav-sel", j === k));
    renderHud();
  }
  function renderHud() {
    const fr = FRAMES[nav.sel];
    const no = nav.typed ? `<b class="typing">${esc(nav.typed)}<i>_</i></b>` : `<b>${NO[DECK[fr.i].id]}</b>`;
    hud.innerHTML = `${no}<span>${esc(titleOf(fr))}</span><em>Type a number · scroll · Enter to open · Esc to go back</em>`;
  }
  const findNo = no => FRAMES.findIndex(fr => NO[DECK[fr.i].id] === no);
  /* typed digits select as you type ("2", "4" lands on 24); A then digits for the appendix; a 1.5 s pause starts over */
  function typeKey(ch) {
    clearTimeout(nav.typedTimer);
    nav.typed = (nav.typed + ch).slice(-2);
    const k = nav.typed[0] === "A" ? findNo(nav.typed) : findNo(nav.typed.padStart(2, "0"));
    if (k >= 0) select(k); else renderHud();
    nav.typedTimer = setTimeout(() => { if (nav) { nav.typed = ""; renderHud(); } }, 1500);
  }
  function openNav() {
    if (nav) return;
    const here = position();
    nav = { sel: FRAMES.findIndex(fr => fr.f === (DECK[here.i].frame || DECK[here.i].id)), typed: "", from: here, wheel: 0 };
    Reveal.configure({ keyboard: false });
    document.body.classList.add("nav-open");
    const rows = Math.ceil(FRAMES.length / COLS);
    FRAMES.forEach((fr, k) => {
      if (!fr.el) return;
      const [x, y] = gridPos(k);
      fr.el.style.transitionDelay = (Math.abs(k - nav.sel) * 14) + "ms";
      fr.el.style.left = x + "px"; fr.el.style.top = y + "px";
      let lab = fr.el.querySelector(":scope > .navlabel");
      if (!lab) { lab = document.createElement("div"); lab.className = "navlabel"; fr.el.appendChild(lab); }
      lab.innerHTML = `<b>${NO[DECK[fr.i].id]}</b> ${esc(titleOf(fr))}`;
    });
    apply(here.cur, false, true);
    const gw = COLS * CELL_W - (CELL_W - 1920), gh = rows * CELL_H - (CELL_H - 1080) + 160;
    const z = Math.min(W / gw, (H - 120) / gh) * 0.96;
    flyTo([gw / 2, gh / 2 + 30, z], true, 1300);
    select(nav.sel);
  }
  function closeNav(k) {
    if (!nav) return;
    const target = k == null ? null : FRAMES[k];
    clearTimeout(nav.typedTimer);
    const from = nav.from; const [gx, gy] = gridPos(k == null ? nav.sel : k);
    const focus = target || FRAMES[FRAMES.findIndex(fr => fr.f === (DECK[from.i].frame || DECK[from.i].id))];
    const [fx, fy] = gridPos(FRAMES.indexOf(focus));
    document.body.classList.add("nav-leaving"); FRAMES.forEach(fr => fr.el && fr.el.classList.toggle("nav-focus", fr === focus));
    flyTo([fx + 960, fy + 540, 1], true, 1050);                  // dive into the chosen frame where it sits in the grid
    const done = () => {
      document.body.classList.add("nav-snap");                  // then swap the layout back underneath, invisibly
      FRAMES.forEach(fr => { if (!fr.el) return; const p = FRAME_POS[fr.f]; fr.el.style.transitionDelay = "0ms"; fr.el.style.left = p[0] + "px"; fr.el.style.top = p[1] + "px"; fr.el.classList.remove("nav-sel", "nav-focus"); });
      document.body.classList.remove("nav-open", "nav-leaving");
      nav = null; Reveal.configure({ keyboard: true });
      if (target && target.i !== from.i) { back.push([from.i, from.step]); jumping = true; Reveal.slide(target.i, 0, -1); jumping = false; update(false); }
      else { apply(position().cur, false); flyTo(camFor(DECK[position().i], position().step), false); }
      requestAnimationFrame(() => requestAnimationFrame(() => document.body.classList.remove("nav-snap")));
    };
    setTimeout(done, 1120);
  }
  addEventListener("keydown", e => {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    if (!nav) { if ((e.key === "m" || e.key === "M") && !e.repeat) { e.preventDefault(); openNav(); } return; }
    e.preventDefault(); e.stopPropagation();
    if (e.key === "Escape" || e.key === "m" || e.key === "M") return closeNav(null);
    if (document.body.classList.contains("nav-leaving")) return;
    if (e.key === "Enter") return closeNav(nav.sel);
    if (e.key === "Backspace") { nav.typed = nav.typed.slice(0, -1); return renderHud(); }
    if (/^[0-9aA]$/.test(e.key)) return typeKey(e.key.toUpperCase());
    const mv = { ArrowRight: 1, ArrowLeft: -1, ArrowDown: COLS, ArrowUp: -COLS, PageDown: COLS, PageUp: -COLS, Home: -1e4, End: 1e4 }[e.key];
    if (mv) { nav.typed = ""; select(nav.sel + mv); }
  }, true);
  /* scroll or trackpad: one frame per notch of travel, accumulated, so a trackpad flick does not skip ten */
  addEventListener("wheel", e => {
    if (!nav || document.body.classList.contains("nav-leaving")) return;
    e.preventDefault();
    nav.wheel += Math.abs(e.deltaY) >= Math.abs(e.deltaX) ? e.deltaY : e.deltaX;
    const n = Math.trunc(nav.wheel / 60);
    if (n) { nav.wheel -= n * 60; nav.typed = ""; select(nav.sel + n); }
  }, { passive: false });
  FRAMES.forEach((fr, k) => { if (!fr.el) return;
    fr.el.addEventListener("mouseenter", () => nav && !document.body.classList.contains("nav-leaving") && select(k));
    fr.el.addEventListener("click", e => { if (!nav || document.body.classList.contains("nav-leaving")) return; e.stopPropagation(); closeNav(k); });
  });

  Reveal.initialize({
    width: W, height: H, hash: true, controls: false, progress: false, center: false,
    transition: "none", backgroundTransition: "none", overview: false, help: false, touch: false,
    scrollActivationWidth: null, /* Reveal 5 switches narrow (portrait phone) viewports to scroll view; keep the canvas */
    plugins: [RevealNotes],
  });
  Reveal.on("ready", () => { update(false); document.body.classList.add("ready"); });
  ["slidechanged", "fragmentshown", "fragmenthidden"].forEach(ev => Reveal.on(ev, () => update(true)));

  /* ---------- touch: tap the left 30% to go back, elsewhere to advance; swipe left/right.
     Touch only (mouse, keyboard and clickers are untouched). Skips pinches, zoomed-in viewports (panning),
     and anything interactive: a, button, form fields, or an element marked data-no-nav. ---------- */
  /* touch events, not pointer events: the browser may claim a horizontal drag as a pan and cancel the pointer */
  let gesture = null;
  addEventListener("touchstart", e => {
    if (e.touches.length !== 1 || nav) { gesture = null; return; }
    const t = e.touches[0];
    const zoomed = window.visualViewport && visualViewport.scale > 1.05;
    const skip = e.target.closest && e.target.closest("a, button, input, textarea, select, [data-no-nav]");
    gesture = zoomed || skip ? null : { x: t.clientX, y: t.clientY, time: performance.now() };
  }, { passive: true });
  addEventListener("touchmove", e => { if (e.touches.length > 1) gesture = null; }, { passive: true });
  addEventListener("touchcancel", () => { gesture = null; }, { passive: true });
  addEventListener("touchend", e => {
    const g = gesture; gesture = null;
    if (!g || e.touches.length) return;
    const t = e.changedTouches[0], dx = t.clientX - g.x, dy = t.clientY - g.y, dt = performance.now() - g.time;
    if (Math.abs(dx) > 50 && Math.abs(dx) > 1.5 * Math.abs(dy) && dt < 800) { dx < 0 ? Reveal.next() : Reveal.prev(); return; }
    if (Math.hypot(dx, dy) < 12 && dt < 400) { g.x < innerWidth * 0.3 ? Reveal.prev() : Reveal.next(); }
  }, { passive: true });

  /* test hook for the screenshot harness */
  window.deckGoto = (i, step) => { jumping = true; Reveal.slide(i, 0, step - 1); jumping = false; update(false); };
})();
