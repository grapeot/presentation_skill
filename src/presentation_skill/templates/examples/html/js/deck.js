/* Slide table in speaking order. steps = clicks inside the slide (1 = no fragments).
   frame defaults to id; frames are laid out on the sheet in this order by js/engine.js.
   cam (optional) = [dx, dy, zoom] relative to the frame centre, or one entry per step. */
(function () {
  const S = (id, part, steps, cam) => ({ id, part, steps, cam });
  window.DECK = [
    S("title", "", 1),
    S("pipeline", "I · Draw it", 3),
    S("split", "II · Split it", 3, [[0, 0, 1], [60, 20, 1.06], [60, 20, 1.06]]),
    S("numbers", "III · Measure it", 3),
    S("close", "IV · Say it", 2),
  ];
})();
