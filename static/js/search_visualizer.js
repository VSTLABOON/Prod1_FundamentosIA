/**
 * search_visualizer.js
 * Simulador visual intuitivo (en 1-2 clics): "Ruta de un robot en el almacen".
 *
 * - 1 clic en cualquiera de los 4 algoritmos ejecuta y anima el recorrido al instante.
 * - 1 clic en cualquier casilla del mapa agrega o quita un estante y recalcula la ruta.
 */

document.addEventListener("DOMContentLoaded", () => {
  const root = document.getElementById("searchVisualizer");
  if (!root) return;

  const COLS = 15;
  const ROWS = 9;
  const COST = { free: 1, congest: 4 };
  const MOVES = [
    { dx: 0, dy: -1 },
    { dx: 1, dy: 0 },
    { dx: 0, dy: 1 },
    { dx: -1, dy: 0 }
  ];

  const ALGO_COPY = {
    astar: {
      name: "A*",
      explain: "A* suma lo que ya camino mas lo que falta hacia la meta. Por eso rodea las zonas de trafico lento y encuentra la ruta mas economica revisando pocas casillas."
    },
    bfs: {
      name: "Busqueda Ciega (BFS)",
      explain: "BFS busca el camino con menos pasos sin saber donde esta la meta ni cuanto cuesta el trafico. Termina cruzando por las zonas lentas."
    },
    ucs: {
      name: "Costo Uniforme",
      explain: "Costo Uniforme encuentra la ruta mas barata evitando el trafico, pero como no tiene brújula hacia la meta, revisa casi todo el almacen."
    },
    greedy: {
      name: "Busqueda Voraz",
      explain: "La Busqueda Voraz corre en linea recta hacia la meta revisando muy pocas casillas, pero se mete de lleno en las zonas lentas de trafico."
    }
  };

  const el = {
    grid: document.getElementById("svGrid"),
    algoPills: root.querySelectorAll(".sv-algo-pill"),
    btnRun: document.getElementById("svBtnRun"),
    btnRandom: document.getElementById("svBtnRandom"),
    btnDefault: document.getElementById("svBtnDefault"),
    statExpanded: document.getElementById("svStatExpanded"),
    statCost: document.getElementById("svStatCost"),
    status: document.getElementById("svStatus"),
    explainText: document.getElementById("svExplainText"),
    btnOpenModal: document.getElementById("svBtnOpenModal"),
    modal: document.getElementById("svModal"),
    modalClose: document.getElementById("svModalClose"),
    modalTabs: root.querySelectorAll("[data-sv-tab]"),
    modalPanes: root.querySelectorAll("[data-sv-pane]"),
    compareCards: document.getElementById("svCompareCards"),
    compareNote: document.getElementById("svCompareNote")
  };
  if (!el.grid) return;

  const sim = {
    algo: "astar",
    terrain: new Array(COLS * ROWS).fill("free"),
    base: 0,
    pick: 0,
    pack: 0,
    overlay: new Array(COLS * ROWS).fill(""),
    bot: -1,
    timers: []
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

  function clearTimers() {
    while (sim.timers.length) clearTimeout(sim.timers.pop());
  }

  function buildGrid() {
    el.grid.style.setProperty("--sv-cols", COLS);
    const frag = document.createDocumentFragment();
    for (let i = 0; i < COLS * ROWS; i++) {
      const c = document.createElement("button");
      c.type = "button";
      c.className = "sv-cell";
      c.dataset.idx = i;
      c.setAttribute("aria-label", `Casilla ${i + 1}`);
      frag.appendChild(c);
      cells.push(c);
    }
    el.grid.appendChild(frag);
  }

  function paintCell(i) {
    const c = cells[i];
    let cls = `sv-cell t-${sim.terrain[i]}`;
    if (sim.overlay[i]) cls += ` o-${sim.overlay[i]}`;
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

  function loadDefaultMap() {
    sim.terrain.fill("free");
    // Estantes limpios y faciles de visualizar
    const shelves = [
      [3, 1], [3, 2], [3, 3], [3, 6], [3, 7],
      [7, 1], [7, 2], [7, 5], [7, 6], [7, 7],
      [11, 1], [11, 2], [11, 3], [11, 5], [11, 6]
    ];
    shelves.forEach(([x, y]) => { sim.terrain[idx(x, y)] = "shelf"; });

    // Zona lenta central (trafico de montacargas)
    const slowCells = [
      [4, 4], [5, 4], [6, 4], [5, 5], [6, 5],
      [8, 4], [9, 4], [10, 4], [12, 7], [13, 7]
    ];
    slowCells.forEach(([x, y]) => { sim.terrain[idx(x, y)] = "congest"; });

    sim.base = idx(1, 4);
    sim.pick = idx(9, 6);
    sim.pack = idx(13, 7);
    sim.terrain[sim.pack] = "free";
    // Zona lenta directa hacia E para que se note la diferencia entre rodear vs cruzar
    sim.terrain[idx(10, 6)] = "congest";
    sim.terrain[idx(11, 7)] = "congest";
    sim.terrain[idx(12, 6)] = "congest";
  }

  function loadRandomMap() {
    for (let attempt = 0; attempt < 30; attempt++) {
      sim.terrain.fill("free");
      for (let x = 2; x < COLS - 2; x += 3) {
        for (let y = 1; y < ROWS - 1; y++) {
          if (Math.random() < 0.55) sim.terrain[idx(x, y)] = "shelf";
        }
        const gap = 1 + Math.floor(Math.random() * (ROWS - 2));
        sim.terrain[idx(x, gap)] = "free";
      }
      for (let k = 0; k < 12; k++) {
        const rx = 2 + Math.floor(Math.random() * (COLS - 4));
        const ry = 1 + Math.floor(Math.random() * (ROWS - 2));
        if (sim.terrain[idx(rx, ry)] === "free") sim.terrain[idx(rx, ry)] = "congest";
      }
      sim.base = idx(1, Math.floor(ROWS / 2));
      sim.pick = idx(Math.floor(COLS / 2) + 1, 2 + Math.floor(Math.random() * (ROWS - 4)));
      sim.pack = idx(COLS - 2, 1 + Math.floor(Math.random() * (ROWS - 2)));
      sim.terrain[sim.base] = "free";
      sim.terrain[sim.pick] = "free";
      sim.terrain[sim.pack] = "free";
      if (solveFlow("bfs")) return;
    }
    loadDefaultMap();
  }

  function priorityOf(algo, g, h) {
    if (algo === "astar") return g + h;
    if (algo === "ucs") return g;
    if (algo === "greedy") return h;
    return 0;
  }

  function solveLeg(start, goal, algo) {
    const gScore = new Map([[start, 0]]);
    const parent = new Map([[start, -1]]);
    const explored = new Set();
    const visitedOrder = [];
    let order = 0;
    let frontier = [{ i: start, g: 0, h: manhattan(start, goal), f: priorityOf(algo, 0, manhattan(start, goal)), order: order++ }];

    while (frontier.length > 0) {
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
        if (explored.has(node.i) || node.g > gScore.get(node.i)) continue;
      }

      explored.add(node.i);
      visitedOrder.push(node.i);

      if (node.i === goal) {
        const path = [];
        let cur = goal;
        while (cur !== -1 && cur !== undefined) {
          path.push(cur);
          cur = parent.get(cur);
        }
        path.reverse();
        let cost = 0;
        for (let k = 1; k < path.length; k++) cost += COST[sim.terrain[path[k]]] || 1;
        return { path, cost, visitedOrder };
      }

      const p = xy(node.i);
      for (const mv of MOVES) {
        const nx = p.x + mv.dx, ny = p.y + mv.dy;
        if (!inBounds(nx, ny)) continue;
        const n = idx(nx, ny);
        if (sim.terrain[n] === "shelf") continue;
        const ng = node.g + (COST[sim.terrain[n]] || 1);

        if (algo === "bfs") {
          if (parent.has(n)) continue;
          parent.set(n, node.i);
          gScore.set(n, ng);
          frontier.push({ i: n, g: ng, h: 0, f: 0, order: order++ });
        } else if (!gScore.has(n) || ng < gScore.get(n)) {
          if (explored.has(n)) continue;
          gScore.set(n, ng);
          parent.set(n, node.i);
          const h = manhattan(n, goal);
          frontier.push({ i: n, g: ng, h, f: priorityOf(algo, ng, h), order: order++ });
        }
      }
    }
    return null;
  }

  function solveFlow(algo) {
    const leg1 = solveLeg(sim.base, sim.pick, algo);
    if (!leg1) return null;
    const leg2 = solveLeg(sim.pick, sim.pack, algo);
    if (!leg2) return null;
    return {
      visited: [...leg1.visitedOrder, ...leg2.visitedOrder],
      path: [...leg1.path, ...leg2.path.slice(1)],
      cost: leg1.cost + leg2.cost,
      expanded: leg1.visitedOrder.length + leg2.visitedOrder.length
    };
  }

  function runVisualSimulation() {
    clearTimers();
    sim.overlay.fill("");
    sim.bot = -1;
    paintAll();

    const copy = ALGO_COPY[sim.algo];
    el.explainText.textContent = copy.explain;

    const res = solveFlow(sim.algo);
    const bestRes = solveFlow("astar");

    if (!res) {
      el.statExpanded.textContent = "—";
      el.statCost.textContent = "—";
      el.status.className = "sv-verdict-box error";
      el.status.innerHTML = "<strong>Camino bloqueado:</strong> Hay estantes cerrando el paso. Haz clic en un estante para abrir camino.";
      return;
    }

    el.status.className = "sv-verdict-box";
    el.status.innerHTML = `Buscando ruta con <strong>${copy.name}</strong>...`;

    const stepMs = Math.max(8, Math.min(22, Math.floor(420 / res.visited.length)));

    res.visited.forEach((cellIdx, k) => {
      sim.timers.push(setTimeout(() => {
        sim.overlay[cellIdx] = "explored";
        paintCell(cellIdx);
        el.statExpanded.textContent = k + 1;
      }, k * stepMs));
    });

    const pathStartMs = res.visited.length * stepMs + 40;
    res.path.forEach((cellIdx, k) => {
      sim.timers.push(setTimeout(() => {
        const prev = sim.bot;
        sim.overlay[cellIdx] = "path";
        sim.bot = cellIdx;
        if (prev >= 0) paintCell(prev);
        paintCell(cellIdx);

        if (k === res.path.length - 1) {
          el.statCost.textContent = `${res.cost} pts`;
          const isOptimal = bestRes && res.cost === bestRes.cost;
          el.status.className = `sv-verdict-box ${isOptimal ? "success" : "warn"}`;
          if (isOptimal) {
            el.status.innerHTML = `<strong>Ruta optima encontrada (${res.cost} pts):</strong> Reviso <strong>${res.expanded}</strong> casillas y evito las zonas lentas.`;
          } else {
            const extra = bestRes ? res.cost - bestRes.cost : 0;
            el.status.innerHTML = `<strong>Ruta completada (${res.cost} pts):</strong> Llego al destino, pero gasto <strong>+${extra} pts extra</strong> por cruzar zonas de trafico.`;
          }
        }
      }, pathStartMs + k * 36));
    });
  }

  // Clic en cualquier casilla para poner o quitar un estante al instante
  el.grid.addEventListener("click", (e) => {
    const cell = e.target.closest(".sv-cell");
    if (!cell) return;
    const i = parseInt(cell.dataset.idx, 10);
    if (isMarker(i)) return;
    sim.terrain[i] = sim.terrain[i] === "shelf" ? "free" : "shelf";
    runVisualSimulation();
  });

  // 1 clic en un algoritmo cambia y ejecuta inmediatamente
  el.algoPills.forEach(pill => {
    pill.addEventListener("click", () => {
      sim.algo = pill.dataset.algo;
      el.algoPills.forEach(p => {
        const active = p === pill;
        p.classList.toggle("active", active);
        p.setAttribute("aria-selected", active ? "true" : "false");
      });
      runVisualSimulation();
    });
  });

  el.btnRun.addEventListener("click", runVisualSimulation);
  el.btnRandom.addEventListener("click", () => {
    loadRandomMap();
    runVisualSimulation();
  });
  el.btnDefault.addEventListener("click", () => {
    loadDefaultMap();
    runVisualSimulation();
  });

  /* ==========================================================================
     MODAL COMPACTO POR PESTANAS (COMPARATIVA Y GUIA)
     ========================================================================== */
  function renderModalComparison() {
    if (!el.compareCards || !el.compareNote) return;
    const order = ["astar", "ucs", "bfs", "greedy"];
    const runs = order.map(a => ({ algo: a, name: ALGO_COPY[a].name, res: solveFlow(a) }));
    const valid = runs.filter(r => r.res);

    if (valid.length === 0) {
      el.compareCards.innerHTML = `<div class="sv-how-card"><p>El mapa actual tiene el paso bloqueado por estantes.</p></div>`;
      el.compareNote.textContent = "Quita algun estante en el tablero para comparar los 4 algoritmos.";
      return;
    }

    const minCost = Math.min(...valid.map(r => r.res.cost));
    const maxExp = Math.max(...valid.map(r => r.res.expanded), 1);
    const minOptExp = Math.min(...valid.filter(r => r.res.cost === minCost).map(r => r.res.expanded));

    el.compareCards.innerHTML = runs.map(({ name, res }) => {
      if (!res) {
        return `<div class="sv-comp-item"><strong>${name}</strong><span>Sin ruta</span></div>`;
      }
      const isOpt = res.cost === minCost;
      const isWinner = isOpt && res.expanded === minOptExp;
      const pct = Math.max(8, Math.round((res.expanded / maxExp) * 100));
      return `
        <div class="sv-comp-item ${isWinner ? "winner" : ""}">
          <div class="sv-comp-top">
            <strong>${name}</strong>
            <span class="sv-comp-badge ${isOpt ? "opt" : "sub"}">${isOpt ? "Ruta optima" : "Mas costosa"} (${res.cost} pts)</span>
          </div>
          <div class="sv-comp-bar-track">
            <div class="sv-comp-bar-fill" style="width:${pct}%"></div>
          </div>
          <div class="sv-comp-meta">Reviso <strong>${res.expanded}</strong> casillas &bull; ${res.path.length - 1} pasos</div>
        </div>
      `;
    }).join("");

    const astar = runs.find(r => r.algo === "astar").res;
    const ucs = runs.find(r => r.algo === "ucs").res;
    if (astar && ucs) {
      const diff = ucs.expanded - astar.expanded;
      el.compareNote.innerHTML = `<strong>Conclusion rapida:</strong> A* logra el mismo costo optimo (${astar.cost} pts) que Costo Uniforme, pero ahorra revisar <strong>${Math.max(0, diff)} casillas</strong> gracias a su guia hacia la meta.`;
    }
  }

  function switchModalTab(tabKey) {
    el.modalTabs.forEach(t => {
      const active = t.dataset.svTab === tabKey;
      t.classList.toggle("active", active);
      t.setAttribute("aria-selected", active ? "true" : "false");
    });
    el.modalPanes.forEach(p => {
      const active = p.dataset.svPane === tabKey;
      p.classList.toggle("active", active);
      p.hidden = !active;
    });
  }

  function openSvModal(tabKey = "compare") {
    if (!el.modal) return;
    renderModalComparison();
    switchModalTab(tabKey);
    el.modal.classList.add("open");
    document.body.style.overflow = "hidden";
  }

  function closeSvModal() {
    if (!el.modal) return;
    el.modal.classList.remove("open");
    document.body.style.overflow = "";
  }

  if (el.btnOpenModal) el.btnOpenModal.addEventListener("click", () => openSvModal("compare"));
  if (el.modalClose) el.modalClose.addEventListener("click", closeSvModal);
  if (el.modal) {
    el.modal.addEventListener("click", (e) => {
      if (e.target === el.modal) closeSvModal();
    });
  }
  el.modalTabs.forEach(t => {
    t.addEventListener("click", () => switchModalTab(t.dataset.svTab));
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && el.modal && el.modal.classList.contains("open")) closeSvModal();
  });

  buildGrid();
  loadDefaultMap();
  runVisualSimulation();
});
