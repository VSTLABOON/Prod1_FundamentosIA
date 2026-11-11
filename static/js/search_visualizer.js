/**
 * search_visualizer.js
 * Simulador grafico de algoritmos de busqueda: "Robot de surtido en un almacen".
 *
 * Flujo practico de 3 paradas: Base de carga (B) -> Estante del pedido (P) -> Zona de empaque (E).
 * El plano es una cuadricula (espacio de estados S). Cada celda libre es un estado; las acciones
 * A(s) son los movimientos arriba / derecha / abajo / izquierda; el costo de paso c(s, a, s')
 * depende del terreno de la celda destino (pasillo = 1, zona de montacargas = 4).
 *
 * Algoritmos implementados como generadores (un "yield" por expansion) para poder animarlos:
 *  - BFS        : cola FIFO, ignora los costos (optimo solo en numero de pasos).
 *  - UCS        : cola de prioridad por g(n) (optimo en costo).
 *  - A*         : cola de prioridad por f(n) = g(n) + h(n), h = distancia Manhattan (admisible).
 *  - Voraz      : cola de prioridad por h(n) (rapido, no garantiza optimo).
 *
 * Sin dependencias externas ni emojis.
 */

document.addEventListener("DOMContentLoaded", () => {
  const root = document.getElementById("searchVisualizer");
  if (!root) return;

  /* ==========================================================================
     1. CONFIGURACION DEL ESPACIO DE ESTADOS
     ========================================================================== */
  const COLS = 24;
  const ROWS = 14;
  const TERRAIN_COST = { free: 1, congest: 4 };
  const SECONDS_PER_COST_UNIT = 3; // Tiempo estimado del robot por unidad de costo
  const MOVES = [
    { dx: 0, dy: -1, name: "arriba" },
    { dx: 1, dy: 0, name: "derecha" },
    { dx: 0, dy: 1, name: "abajo" },
    { dx: -1, dy: 0, name: "izquierda" }
  ];
  const SPEED_DELAYS = [420, 280, 180, 120, 80, 50, 30, 16, 8, 0];

  const ALGO_INFO = {
    astar: {
      name: "A*",
      formula: "f(n) = g(n) + h(n)",
      title: "Como decide A*",
      text: "Siempre expande el nodo de la frontera con menor f(n): el costo real ya recorrido g(n) mas una estimacion h(n) de lo que falta (distancia Manhattan hasta la meta). Como h(n) nunca sobreestima el costo real (cada paso cuesta al menos 1), la heuristica es admisible y A* garantiza la ruta de menor costo explorando muchas menos celdas que UCS."
    },
    ucs: {
      name: "Costo uniforme",
      formula: "f(n) = g(n)",
      title: "Como decide Costo Uniforme",
      text: "Expande siempre el nodo con menor costo acumulado g(n), sin mirar hacia donde esta la meta. Por eso crece como una mancha en todas direcciones, pero rodea las zonas de montacargas cuando le resultan caras. Garantiza la ruta de menor costo, a cambio de explorar mas celdas que A*."
    },
    bfs: {
      name: "BFS",
      formula: "cola FIFO (por niveles)",
      title: "Como decide BFS (anchura)",
      text: "Expande los nodos en el orden en que fueron descubiertos, nivel por nivel. Encuentra la ruta con menos pasos, pero ignora que las zonas de montacargas cuestan 4: si el camino mas corto pasa por ahi, lo tomara aunque sea mas lento y caro. Es busqueda ciega: no usa informacion de la meta."
    },
    greedy: {
      name: "Voraz",
      formula: "f(n) = h(n)",
      title: "Como decide la busqueda Voraz",
      text: "Solo mira la heuristica h(n): corre hacia la celda que parece estar mas cerca de la meta, ignorando lo que ya costo llegar. Suele expandir muy pocos nodos, pero puede atravesar zonas caras o meterse en callejones entre estantes, por lo que no garantiza la ruta optima."
    }
  };

  /* ==========================================================================
     2. REFERENCIAS AL DOM
     ========================================================================== */
  const el = {
    grid: document.getElementById("svGrid"),
    algorithm: document.getElementById("svAlgorithm"),
    speed: document.getElementById("svSpeed"),
    speedValue: document.getElementById("svSpeedValue"),
    toolBtns: root.querySelectorAll(".sv-tool-btn"),
    btnRun: document.getElementById("svBtnRun"),
    btnStep: document.getElementById("svBtnStep"),
    btnReset: document.getElementById("svBtnReset"),
    btnCompare: document.getElementById("svBtnCompare"),
    btnDefault: document.getElementById("svBtnDefault"),
    btnRandom: document.getElementById("svBtnRandom"),
    btnClear: document.getElementById("svBtnClear"),
    status: document.getElementById("svStatus"),
    statLeg: document.getElementById("svStatLeg"),
    statExpanded: document.getElementById("svStatExpanded"),
    statFrontier: document.getElementById("svStatFrontier"),
    statCost: document.getElementById("svStatCost"),
    nodeFormula: document.getElementById("svNodeFormula"),
    nodeDetail: document.getElementById("svNodeDetail"),
    explainTitle: document.getElementById("svExplainTitle"),
    explainText: document.getElementById("svExplainText"),
    log: document.getElementById("svLog"),
    compareBox: document.getElementById("svCompareBox"),
    compareBody: document.getElementById("svCompareBody"),
    compareNote: document.getElementById("svCompareNote"),
    flowSteps: root.querySelectorAll(".sv-flow-step")
  };
  if (!el.grid) return;

  /* ==========================================================================
     3. ESTADO DEL SIMULADOR
     ========================================================================== */
  const sim = {
    terrain: new Array(COLS * ROWS).fill("free"), // "free" | "shelf" | "congest"
    base: 0,
    pick: 0,
    pack: 0,
    overlay: new Array(COLS * ROWS).fill(""),     // "" | "frontier" | "explored" | "path"
    current: -1,
    bot: -1,
    tool: "shelf",
    generator: null,
    timer: null,
    botTimer: null,
    running: false,
    finished: false,
    expandedTotal: 0,
    finishedLegsCost: 0
  };
  const cells = [];

  const idx = (x, y) => y * COLS + x;
  const xy = (i) => ({ x: i % COLS, y: Math.floor(i / COLS) });
  const inBounds = (x, y) => x >= 0 && y >= 0 && x < COLS && y < ROWS;
  const manhattan = (a, b) => {
    const pa = xy(a), pb = xy(b);
    return Math.abs(pa.x - pb.x) + Math.abs(pa.y - pb.y);
  };
  const isMarker = (i) => i === sim.base || i === sim.pick || i === sim.pack;
  const fmt = (i) => { const p = xy(i); return `(${p.x}, ${p.y})`; };

  /* ==========================================================================
     4. CONSTRUCCION Y RENDERIZADO DE LA CUADRICULA
     ========================================================================== */
  function buildGrid() {
    el.grid.style.setProperty("--sv-cols", COLS);
    const frag = document.createDocumentFragment();
    for (let i = 0; i < COLS * ROWS; i++) {
      const c = document.createElement("div");
      c.className = "sv-cell";
      c.dataset.idx = i;
      frag.appendChild(c);
      cells.push(c);
    }
    el.grid.appendChild(frag);
  }

  function paintCell(i) {
    const c = cells[i];
    let cls = `sv-cell t-${sim.terrain[i]}`;
    if (sim.overlay[i]) cls += ` o-${sim.overlay[i]}`;
    if (i === sim.current) cls += " o-current";
    let label = "";
    if (i === sim.base) { cls += " m-base"; label = "B"; }
    else if (i === sim.pick) { cls += " m-pick"; label = "P"; }
    else if (i === sim.pack) { cls += " m-pack"; label = "E"; }
    if (i === sim.bot) cls += " o-bot";
    if (c.className !== cls) c.className = cls;
    if (c.textContent !== label) c.textContent = label;
  }

  function paintAll() {
    for (let i = 0; i < cells.length; i++) paintCell(i);
  }

  /* ==========================================================================
     5. ALMACENES PREDEFINIDOS
     ========================================================================== */
  function loadDefaultWarehouse() {
    sim.terrain.fill("free");
    // Bloques de estanteria verticales separados por pasillos
    const shelfCols = [3, 4, 7, 8, 11, 12, 15, 16, 19, 20];
    shelfCols.forEach(x => {
      for (let y = 2; y <= 5; y++) sim.terrain[idx(x, y)] = "shelf";
      for (let y = 8; y <= 11; y++) sim.terrain[idx(x, y)] = "shelf";
    });
    // Pasillo central ocupado por montacargas (costo alto)
    for (let x = 6; x <= 13; x++) {
      for (let y = 6; y <= 7; y++) sim.terrain[idx(x, y)] = "congest";
    }
    // Zona de maniobra de montacargas frente al area de empaque
    for (let x = 17; x <= 22; x++) {
      for (let y = 12; y <= 13; y++) sim.terrain[idx(x, y)] = "congest";
    }
    sim.base = idx(1, 6);
    sim.pick = idx(14, 10);
    sim.pack = idx(23, 12);
  }

  function loadRandomWarehouse() {
    for (let attempt = 0; attempt < 40; attempt++) {
      sim.terrain.fill("free");
      // Estanterias con huecos aleatorios
      for (let x = 2; x < COLS - 2; x += 4) {
        const width = Math.random() < 0.5 ? 1 : 2;
        for (let w = 0; w < width; w++) {
          for (let y = 1; y < ROWS - 1; y++) {
            if (Math.random() < 0.82) sim.terrain[idx(x + w, y)] = "shelf";
          }
        }
        // Garantizar al menos un cruce horizontal en cada bloque
        const gap = 2 + Math.floor(Math.random() * (ROWS - 4));
        for (let w = 0; w < width; w++) sim.terrain[idx(x + w, gap)] = "free";
      }
      // Zonas de montacargas
      const zones = 2 + Math.floor(Math.random() * 3);
      for (let z = 0; z < zones; z++) {
        const zx = Math.floor(Math.random() * (COLS - 5));
        const zy = Math.floor(Math.random() * (ROWS - 3));
        const zw = 2 + Math.floor(Math.random() * 4);
        const zh = 2 + Math.floor(Math.random() * 2);
        for (let x = zx; x < zx + zw; x++) {
          for (let y = zy; y < zy + zh; y++) {
            if (inBounds(x, y) && sim.terrain[idx(x, y)] === "free") sim.terrain[idx(x, y)] = "congest";
          }
        }
      }
      const randomFree = (xMin, xMax) => {
        for (let k = 0; k < 200; k++) {
          const x = xMin + Math.floor(Math.random() * (xMax - xMin + 1));
          const y = Math.floor(Math.random() * ROWS);
          if (sim.terrain[idx(x, y)] === "free") return idx(x, y);
        }
        return -1;
      };
      sim.base = randomFree(0, 1);
      sim.pick = randomFree(8, 16);
      sim.pack = randomFree(COLS - 2, COLS - 1);
      if ([sim.base, sim.pick, sim.pack].includes(-1)) continue;
      if (new Set([sim.base, sim.pick, sim.pack]).size < 3) continue;
      // Validar que el flujo completo sea alcanzable
      if (runSilently("bfs")) return;
    }
    loadDefaultWarehouse();
  }

  function clearWarehouse() {
    sim.terrain.fill("free");
    sim.base = idx(1, 7);
    sim.pick = idx(12, 3);
    sim.pack = idx(22, 11);
  }

  /* ==========================================================================
     6. ALGORITMOS DE BUSQUEDA (GENERADORES PASO A PASO)
     ========================================================================== */
  function priorityOf(algo, g, h) {
    if (algo === "astar") return g + h;
    if (algo === "ucs") return g;
    if (algo === "greedy") return h;
    return 0;
  }

  function reconstructPath(parent, goal) {
    const path = [];
    let cur = goal;
    while (cur !== -1 && cur !== undefined) {
      path.push(cur);
      cur = parent.get(cur);
    }
    return path.reverse();
  }

  function pathCost(path) {
    let cost = 0;
    for (let k = 1; k < path.length; k++) cost += TERRAIN_COST[sim.terrain[path[k]]] || 1;
    return cost;
  }

  /**
   * Busca un tramo start -> goal. Emite un evento por cada nodo expandido.
   * Devuelve { path, cost, expanded } o null si la meta es inalcanzable.
   */
  function* searchLeg(start, goal, algo) {
    const gScore = new Map([[start, 0]]);
    const parent = new Map([[start, -1]]);
    const explored = new Set();
    let order = 0;
    const h0 = manhattan(start, goal);
    let frontier = [{ i: start, g: 0, h: h0, f: priorityOf(algo, 0, h0), order: order++ }];

    while (frontier.length > 0) {
      // Seleccion del siguiente nodo segun la estrategia de la frontera
      let node;
      if (algo === "bfs") {
        node = frontier.shift();
      } else {
        let best = 0;
        for (let k = 1; k < frontier.length; k++) {
          const a = frontier[k], b = frontier[best];
          if (a.f < b.f || (a.f === b.f && (a.h < b.h || (a.h === b.h && a.order < b.order)))) best = k;
        }
        node = frontier.splice(best, 1)[0];
        if (explored.has(node.i) || node.g > gScore.get(node.i)) continue; // Entrada obsoleta
      }

      explored.add(node.i);

      // Prueba de meta GoalTest(s) al extraer el nodo de la frontera
      if (node.i === goal) {
        const path = reconstructPath(parent, goal);
        yield { type: "found", node, path, expanded: explored.size, frontierSize: frontier.length };
        return { path, cost: pathCost(path), expanded: explored.size };
      }

      // Expansion: aplicar acciones A(s) y modelo de transicion Result(s, a)
      const added = [];
      const p = xy(node.i);
      for (const mv of MOVES) {
        const nx = p.x + mv.dx, ny = p.y + mv.dy;
        if (!inBounds(nx, ny)) continue;
        const n = idx(nx, ny);
        if (sim.terrain[n] === "shelf") continue;
        const ng = node.g + (TERRAIN_COST[sim.terrain[n]] || 1);

        if (algo === "bfs") {
          if (parent.has(n)) continue;
          parent.set(n, node.i);
          gScore.set(n, ng);
          frontier.push({ i: n, g: ng, h: 0, f: 0, order: order++ });
          added.push(n);
        } else if (!gScore.has(n) || ng < gScore.get(n)) {
          if (explored.has(n)) continue;
          gScore.set(n, ng);
          parent.set(n, node.i);
          const h = manhattan(n, goal);
          frontier.push({ i: n, g: ng, h, f: priorityOf(algo, ng, h), order: order++ });
          added.push(n);
        }
      }

      yield {
        type: "expand",
        node,
        added,
        expanded: explored.size,
        frontierSize: new Set(frontier.map(f => f.i)).size
      };
    }

    yield { type: "fail", expanded: explored.size };
    return null;
  }

  /** Flujo completo de la tarea: Base -> Pedido -> Empaque. */
  function* runFlow(algo) {
    const legs = [
      { from: sim.base, to: sim.pick, name: "Base \u2192 Pedido" },
      { from: sim.pick, to: sim.pack, name: "Pedido \u2192 Empaque" }
    ];
    const total = { path: [], cost: 0, expanded: 0, legs: [] };

    for (let k = 0; k < legs.length; k++) {
      yield { type: "leg-start", leg: k, name: legs[k].name };
      const res = yield* searchLeg(legs[k].from, legs[k].to, algo);
      if (!res) {
        yield { type: "flow-fail", leg: k, name: legs[k].name };
        return null;
      }
      total.legs.push(res);
      total.path.push(...(k === 0 ? res.path : res.path.slice(1)));
      total.cost += res.cost;
      total.expanded += res.expanded;
      yield { type: "leg-done", leg: k, name: legs[k].name, result: res };
    }

    yield { type: "flow-done", total };
    return total;
  }

  function runSilently(algo) {
    const it = runFlow(algo);
    let r = it.next();
    while (!r.done) r = it.next();
    return r.value;
  }

  /* ==========================================================================
     7. VISUALIZACION DE EVENTOS
     ========================================================================== */
  function setStatus(html, tone = "") {
    el.status.innerHTML = html;
    el.status.className = `sv-status-banner ${tone}`.trim();
  }

  function addLog(text) {
    const li = document.createElement("li");
    li.textContent = text;
    el.log.prepend(li);
    while (el.log.children.length > 7) el.log.lastChild.remove();
  }

  function setFlowHighlight(activeLeg, doneUpTo = -2) {
    el.flowSteps.forEach(step => {
      const leg = parseInt(step.dataset.leg, 10);
      step.classList.toggle("active", leg === activeLeg);
      step.classList.toggle("done", leg <= doneUpTo);
    });
  }

  function describeNode(node, algo) {
    const parts = [`g = ${node.g}`];
    if (algo === "astar" || algo === "greedy") parts.push(`h = ${node.h}`);
    if (algo === "astar") parts.push(`f = ${node.g + node.h}`);
    return parts.join("  \u00b7  ");
  }

  function clearSearchOverlay(keepPath) {
    for (let i = 0; i < sim.overlay.length; i++) {
      if (keepPath && sim.overlay[i] === "path") continue;
      sim.overlay[i] = "";
    }
    sim.current = -1;
  }

  function applyEvent(ev, algo) {
    const prevCurrent = sim.current;

    switch (ev.type) {
      case "leg-start": {
        clearSearchOverlay(true);
        paintAll();
        el.statLeg.textContent = `${ev.leg + 1} / 2`;
        setFlowHighlight(ev.leg, ev.leg - 1);
        setStatus(`Buscando tramo ${ev.leg + 1}: <strong>${ev.name}</strong> con ${ALGO_INFO[algo].name}...`, "running");
        addLog(`Inicia tramo ${ev.leg + 1} (${ev.name}).`);
        break;
      }
      case "expand": {
        const i = ev.node.i;
        if (sim.overlay[i] !== "path") sim.overlay[i] = "explored";
        sim.current = i;
        ev.added.forEach(n => {
          if (sim.overlay[n] !== "path") sim.overlay[n] = "frontier";
          paintCell(n);
        });
        if (prevCurrent >= 0) paintCell(prevCurrent);
        paintCell(i);
        sim.expandedTotal++;
        el.statExpanded.textContent = sim.expandedTotal;
        el.statFrontier.textContent = ev.frontierSize;
        el.nodeDetail.textContent = `Celda ${fmt(i)}  \u00b7  ${describeNode(ev.node, algo)}  \u00b7  +${ev.added.length} vecinos a la frontera`;
        addLog(`Expande ${fmt(i)}  [${describeNode(ev.node, algo)}]`);
        break;
      }
      case "found": {
        sim.expandedTotal++;
        el.statExpanded.textContent = sim.expandedTotal;
        el.nodeDetail.textContent = `GoalTest(${fmt(ev.node.i)}) = verdadero  \u00b7  ${describeNode(ev.node, algo)}`;
        sim.current = -1;
        if (prevCurrent >= 0) paintCell(prevCurrent);
        ev.path.forEach((n, k) => {
          sim.overlay[n] = "path";
          cells[n].style.setProperty("--sv-delay", `${Math.min(k * 18, 900)}ms`);
          paintCell(n);
        });
        break;
      }
      case "leg-done": {
        sim.finishedLegsCost += ev.result.cost;
        el.statCost.textContent = sim.finishedLegsCost;
        addLog(`Tramo ${ev.leg + 1} resuelto: ${ev.result.path.length - 1} pasos, costo ${ev.result.cost}.`);
        break;
      }
      case "fail":
        break;
      case "flow-fail": {
        setFlowHighlight(ev.leg, ev.leg - 1);
        setStatus(`Sin solucion: el tramo <strong>${ev.name}</strong> esta bloqueado por estantes. La frontera se vacio sin cumplir GoalTest.`, "error");
        addLog(`Frontera vacia: tramo ${ev.leg + 1} inalcanzable.`);
        break;
      }
      case "flow-done": {
        const t = ev.total;
        el.statCost.textContent = t.cost;
        el.statFrontier.textContent = "0";
        setFlowHighlight(-9, 1);
        const secs = t.cost * SECONDS_PER_COST_UNIT;
        setStatus(`Ruta completa con ${ALGO_INFO[algo].name}: <strong>${t.path.length - 1} pasos</strong>, costo <strong>${t.cost}</strong> (~${Math.floor(secs / 60)} min ${secs % 60} s) y <strong>${t.expanded}</strong> nodos expandidos.`, "success");
        animateRobot(t.path);
        break;
      }
    }
  }

  function animateRobot(path) {
    clearInterval(sim.botTimer);
    let k = 0;
    sim.botTimer = setInterval(() => {
      const prev = sim.bot;
      if (k >= path.length) {
        clearInterval(sim.botTimer);
        sim.bot = -1;
        if (prev >= 0) paintCell(prev);
        return;
      }
      sim.bot = path[k];
      if (prev >= 0) paintCell(prev);
      paintCell(sim.bot);
      if (path[k] === sim.pick) addLog("El robot recoge el pedido en el estante.");
      k++;
    }, 70);
  }

  /* ==========================================================================
     8. CONTROL DE EJECUCION (EJECUTAR / PAUSAR / PASO A PASO / REINICIAR)
     ========================================================================== */
  function currentAlgo() {
    return el.algorithm ? el.algorithm.value : "astar";
  }

  function resetRun(silent = false) {
    clearTimeout(sim.timer);
    clearInterval(sim.botTimer);
    sim.generator = null;
    sim.running = false;
    sim.finished = false;
    sim.bot = -1;
    sim.expandedTotal = 0;
    sim.finishedLegsCost = 0;
    clearSearchOverlay(false);
    cells.forEach(c => c.style.removeProperty("--sv-delay"));
    paintAll();
    el.btnRun.textContent = "Ejecutar busqueda";
    el.statLeg.textContent = "\u2014";
    el.statExpanded.textContent = "0";
    el.statFrontier.textContent = "0";
    el.statCost.textContent = "\u2014";
    el.nodeDetail.textContent = "Aun no se ha expandido ningun nodo.";
    setFlowHighlight(-9);
    if (!silent) {
      el.log.innerHTML = "";
      setStatus("Listo. Pulsa <strong>Ejecutar busqueda</strong> o edita el plano.");
    }
  }

  function ensureGenerator() {
    if (!sim.generator || sim.finished) {
      resetRun(true);
      el.log.innerHTML = "";
      sim.generator = runFlow(currentAlgo());
    }
  }

  /** Avanza hasta el siguiente nodo expandido (o fin). Devuelve false si termino. */
  function stepOnce() {
    const algo = currentAlgo();
    while (true) {
      const r = sim.generator.next();
      if (r.done) {
        finishRun();
        return false;
      }
      applyEvent(r.value, algo);
      if (r.value.type === "expand" || r.value.type === "found") return true;
      if (r.value.type === "flow-done" || r.value.type === "flow-fail") {
        finishRun();
        return false;
      }
    }
  }

  function finishRun() {
    clearTimeout(sim.timer);
    sim.running = false;
    sim.finished = true;
    el.btnRun.textContent = "Ejecutar de nuevo";
  }

  function tick() {
    if (!sim.running) return;
    const delay = SPEED_DELAYS[(parseInt(el.speed.value, 10) || 6) - 1];
    const stepsPerTick = delay === 0 ? 6 : 1;
    for (let s = 0; s < stepsPerTick; s++) {
      if (!stepOnce()) return;
    }
    sim.timer = setTimeout(tick, delay);
  }

  function toggleRun() {
    if (sim.running) {
      sim.running = false;
      clearTimeout(sim.timer);
      el.btnRun.textContent = "Continuar";
      setStatus("Busqueda en pausa. Usa <strong>Paso a paso</strong> para inspeccionar cada expansion.", "paused");
      return;
    }
    ensureGenerator();
    sim.running = true;
    el.btnRun.textContent = "Pausar";
    tick();
  }

  function stepManual() {
    if (sim.running) {
      sim.running = false;
      clearTimeout(sim.timer);
      el.btnRun.textContent = "Continuar";
    }
    ensureGenerator();
    stepOnce();
  }

  /* ==========================================================================
     9. COMPARATIVA ENTRE ALGORITMOS SOBRE EL MISMO PLANO
     ========================================================================== */
  function compareAll() {
    const order = ["bfs", "greedy", "ucs", "astar"];
    const results = order.map(a => ({ algo: a, res: runSilently(a) }));
    const valid = results.filter(r => r.res);
    if (valid.length === 0) {
      el.compareBox.hidden = false;
      el.compareBody.innerHTML = "";
      el.compareNote.textContent = "Ningun algoritmo encontro solucion: el flujo esta bloqueado por estantes.";
      return;
    }
    const minCost = Math.min(...valid.map(r => r.res.cost));
    const minExp = Math.min(...valid.filter(r => r.res.cost === minCost).map(r => r.res.expanded));

    el.compareBody.innerHTML = results.map(({ algo, res }) => {
      if (!res) {
        return `<tr><td>${ALGO_INFO[algo].name}</td><td colspan="4">Sin solucion</td></tr>`;
      }
      const optimal = res.cost === minCost;
      const best = optimal && res.expanded === minExp;
      const secs = res.cost * SECONDS_PER_COST_UNIT;
      return `<tr class="${best ? "sv-row-best" : ""}">
        <td>${ALGO_INFO[algo].name}${optimal ? ' <span class="sv-opt-tag">optimo</span>' : ""}</td>
        <td>${res.expanded}</td>
        <td>${res.path.length - 1}</td>
        <td>${res.cost}</td>
        <td>${Math.floor(secs / 60)}:${String(secs % 60).padStart(2, "0")} min</td>
      </tr>`;
    }).join("");

    const astar = results.find(r => r.algo === "astar").res;
    const ucs = results.find(r => r.algo === "ucs").res;
    const bfs = results.find(r => r.algo === "bfs").res;
    let note = "";
    if (astar && ucs) {
      const saved = ucs.expanded - astar.expanded;
      note += `A* llega al mismo costo optimo que UCS expandiendo ${saved >= 0 ? saved + " nodos menos" : Math.abs(saved) + " nodos mas"} gracias a la heuristica. `;
    }
    if (bfs && astar && bfs.cost > astar.cost) {
      note += `BFS encuentra una ruta de ${bfs.path.length - 1} pasos pero cuesta ${bfs.cost - astar.cost} unidades mas porque atraviesa zonas de montacargas.`;
    } else if (bfs && astar) {
      note += "En este plano la ruta mas corta en pasos coincide con la de menor costo, por eso BFS tambien resulta optima.";
    }
    const greedy = results.find(r => r.algo === "greedy").res;
    if (greedy && astar && greedy.cost > astar.cost) {
      note += ` La busqueda Voraz solo expande ${greedy.expanded} nodos, pero al ignorar g(n) su ruta cuesta ${greedy.cost} frente a ${astar.cost}.`;
    }
    el.compareNote.textContent = note;
    el.compareBox.hidden = false;
  }

  /* ==========================================================================
     10. EDICION INTERACTIVA DEL PLANO (CLIC Y ARRASTRE)
     ========================================================================== */
  let painting = false;
  let paintMode = null;

  function applyTool(i) {
    const tool = sim.tool;
    if (tool === "base" || tool === "pick" || tool === "pack") {
      if (isMarker(i) && sim[tool] !== i) return;
      const prev = sim[tool];
      sim[tool] = i;
      sim.terrain[i] = "free";
      paintCell(prev);
      paintCell(i);
      return;
    }
    if (isMarker(i)) return;
    const target = tool === "erase" ? "free" : tool;
    // El primer clic define si se pinta o se borra durante el arrastre
    if (paintMode === null) paintMode = sim.terrain[i] === target && tool !== "erase" ? "free" : target;
    sim.terrain[i] = paintMode;
    paintCell(i);
  }

  function cellFromEvent(e) {
    const target = document.elementFromPoint(e.clientX, e.clientY);
    if (!target || !target.classList.contains("sv-cell")) return -1;
    return parseInt(target.dataset.idx, 10);
  }

  function onEditStart() {
    if (sim.generator || sim.finished) resetRun(true);
    el.compareBox.hidden = true;
  }

  el.grid.addEventListener("pointerdown", (e) => {
    const i = cellFromEvent(e);
    if (i < 0) return;
    e.preventDefault();
    onEditStart();
    painting = true;
    paintMode = null;
    applyTool(i);
  });

  el.grid.addEventListener("pointermove", (e) => {
    if (!painting) return;
    const i = cellFromEvent(e);
    if (i >= 0) applyTool(i);
  });

  const stopPainting = () => {
    if (painting) setStatus("Plano editado. Pulsa <strong>Ejecutar busqueda</strong> para recalcular la ruta.");
    painting = false;
    paintMode = null;
  };
  window.addEventListener("pointerup", stopPainting);
  window.addEventListener("pointercancel", stopPainting);

  el.toolBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      sim.tool = btn.dataset.tool;
      el.toolBtns.forEach(b => {
        const on = b === btn;
        b.classList.toggle("active", on);
        b.setAttribute("aria-checked", on ? "true" : "false");
      });
    });
  });

  /* ==========================================================================
     11. EVENTOS DE CONTROLES Y ARRANQUE
     ========================================================================== */
  function updateExplanation() {
    const info = ALGO_INFO[currentAlgo()];
    el.explainTitle.textContent = info.title;
    el.explainText.textContent = info.text;
    el.nodeFormula.textContent = info.formula;
  }

  el.algorithm.addEventListener("change", () => {
    updateExplanation();
    resetRun();
  });
  el.speed.addEventListener("input", () => {
    el.speedValue.textContent = el.speed.value;
  });
  el.btnRun.addEventListener("click", toggleRun);
  el.btnStep.addEventListener("click", stepManual);
  el.btnReset.addEventListener("click", () => resetRun());
  el.btnCompare.addEventListener("click", compareAll);
  el.btnDefault.addEventListener("click", () => {
    loadDefaultWarehouse();
    el.compareBox.hidden = true;
    resetRun();
  });
  el.btnRandom.addEventListener("click", () => {
    loadRandomWarehouse();
    el.compareBox.hidden = true;
    resetRun();
    setStatus("Almacen aleatorio generado (con flujo alcanzable). Pulsa <strong>Ejecutar busqueda</strong>.");
  });
  el.btnClear.addEventListener("click", () => {
    clearWarehouse();
    el.compareBox.hidden = true;
    resetRun();
    setStatus("Plano vacio. Dibuja estantes y zonas de montacargas para crear tu propio almacen.");
  });

  buildGrid();
  loadDefaultWarehouse();
  updateExplanation();
  resetRun();
});
