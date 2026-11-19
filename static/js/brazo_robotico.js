/**
 * brazo_robotico.js
 * Celda Industrial 3D (Three.js) con tareas practicas reales:
 *  A) Pick & Place (recoger pieza de banda y llevarla a la prensa)
 *  B) Soldadura Multi-Punto en secuencia
 *  C) Obstaculo imprevisto con recalculo en vivo desde la postura actual
 *  + Vista previa directa: pasar el cursor por el mapa muestra la postura en 3D
 */

document.addEventListener("DOMContentLoaded", () => {
  const card = document.getElementById("robotArmCard");
  if (!card) return;

  const SCALE = 30.0;
  const BASE_2D = [220, 215];
  const L1_2D = 95;
  const L2_2D = 80;
  const L1_3D = L1_2D / SCALE;
  const L2_3D = L2_2D / SCALE;

  const THREE_CDN_URL = "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js";
  let threeLoadPromise = null;

  const el = {
    presetButtons: document.getElementById("armPresetButtons"),
    algoPills: card.querySelectorAll(".arm-algo-pill"),
    btnEmergency: document.getElementById("armBtnEmergency"),
    btnHistory: document.getElementById("armBtnHistory"),
    historyCount: document.getElementById("armHistoryCount"),
    btnCompare: document.getElementById("armBtnCompare"),
    btnReset: document.getElementById("armBtnReset"),
    btnPlayPause: document.getElementById("armBtnPlayPause"),
    btnReplay: document.getElementById("armBtnReplay"),
    phaseBadge: document.getElementById("armPhaseBadge"),
    phaseFill: document.getElementById("armPhaseFill"),
    cargoSelect: document.getElementById("armCargoSelect"),
    speedBtns: card.querySelectorAll(".arm-speed-btn"),
    camBtns: card.querySelectorAll(".arm-cam-btn"),
    container3d: document.getElementById("arm3dContainer"),
    hoverHud: document.getElementById("armHoverHud"),
    telemetryHud: document.getElementById("armTelemetryHud"),
    csCanvas: document.getElementById("armCspaceCanvas"),
    statExpanded: document.getElementById("armStatExpanded"),
    statEnergy: document.getElementById("armStatEnergy"),
    statStatus: document.getElementById("armStatStatus"),
    kpiStatusBox: document.getElementById("armKpiStatusBox"),
    verdictBox: document.getElementById("armVerdictBox"),
    verdictText: document.getElementById("armVerdictText"),
    compareModal: document.getElementById("armCompareModal"),
    compareClose: document.getElementById("armCompareClose"),
    compareBody: document.getElementById("armCompareBody"),
    compareCards: document.getElementById("armCompareCards"),
    compareSummary: document.getElementById("armCompareSummary"),
    switchToLog: document.getElementById("armSwitchToLog"),
    logModal: document.getElementById("armLogModal"),
    logClose: document.getElementById("armLogClose"),
    switchToCompare: document.getElementById("armSwitchToCompare"),
    logTabs: document.querySelectorAll("#armLogModal [data-arm-tab]"),
    logPanes: document.querySelectorAll("#armLogModal [data-arm-pane]"),
    ragChips: document.querySelectorAll("#armLogModal [data-rag-q]"),
    ragForm: document.getElementById("armRagForm"),
    ragInput: document.getElementById("armRagInput"),
    ragSubmit: document.getElementById("armRagSubmit"),
    ragAnswer: document.getElementById("armRagAnswer"),
    ragSources: document.getElementById("armRagSources"),
    sqlTotal: document.getElementById("armSqlTotal"),
    sqlFailures: document.getElementById("armSqlFailures"),
    sqlCached: document.getElementById("armSqlCached"),
    sqlSavings: document.getElementById("armSqlSavings"),
    sqlFilters: document.querySelectorAll("#armLogModal [data-sql-filter]"),
    btnClearRuns: document.getElementById("armBtnClearRuns"),
    runsList: document.getElementById("armRunsList"),
    cargoDelivered: document.getElementById("armCargoDelivered"),
    cargoKg: document.getElementById("armCargoKg"),
    cargoMeters: document.getElementById("armCargoMeters"),
    cargoAborted: document.getElementById("armCargoAborted"),
    cargoList: document.getElementById("armCargoList"),
    toggleMemory: document.getElementById("armToggleMemory"),
    btnClearCache: document.getElementById("armBtnClearCache"),
    cacheList: document.getElementById("armCacheList")
  };

  const csCtx = el.csCanvas.getContext("2d");

  const state = {
    meta: null,
    activeTaskId: "pick_and_place",
    algorithm: "astar",
    cargoId: "battery_module",
    startDeg: [170, 15],
    waypoints: [],
    obstacles: [],
    unexpectedSpec: null,
    unexpectedActive: false,
    useMemory: true,
    sqlFilter: "all",
    lastResult: null,
    stageIdx: 0,
    completedWaypoints: 0,
    fromWaypointOffset: 0,
    carryingPart: false,
    deliveredPart: false,
    reqSeq: 0,
    compareReqSeq: 0,
    historyReqSeq: 0,
    ragReqSeq: 0,
    historyDirty: true,
    historyLoadedFilter: null,
    speed: 1.0,
    paused: false,
    phase: "idle", // 'idle' | 'exploring' | 'moving' | 'dwell' | 'done' | 'failed'
    dwellLeftMs: 0,
    pendingNextStage: null,
    activated: false,
    uiBound: false,
    threePointerBound: false,
    expCursor: 0,
    pathCursor: 0,
    liveDeg: [170, 15],
    cspaceHover: null, // { i1, i2, val }
    lastTickTime: 0,
    rafId: null,
    lastFocusedEl: null,
    confirmTimers: {}
  };

  const cspaceBaseCanvas = document.createElement("canvas");
  cspaceBaseCanvas.width = el.csCanvas.width;
  cspaceBaseCanvas.height = el.csCanvas.height;
  const cspaceBaseCtx = cspaceBaseCanvas.getContext("2d");
  let cachedBaseStageKey = "";

  const cspaceExploredCanvas = document.createElement("canvas");
  cspaceExploredCanvas.width = el.csCanvas.width;
  cspaceExploredCanvas.height = el.csCanvas.height;
  const cspaceExploredCtx = cspaceExploredCanvas.getContext("2d");
  let cachedExploredKey = "";
  let cachedExploredCount = 0;

  const three = {
    ready: false,
    scene: null,
    camera: null,
    renderer: null,
    camTheta: 0.48,
    camPhi: 0.80,
    camRadius: 13.6,
    targetCamTheta: 0.48,
    targetCamPhi: 0.80,
    targetCamRadius: 13.6,
    shoulderGroup: null,
    elbowGroup: null,
    ghostShoulder: null,
    ghostElbow: null,
    ghostMat: null,
    torchLight: null,
    statusRing: null,
    emergencyBeacons: [],
    gripperLeft: null,
    gripperRight: null,
    clampHalo: null,
    cargoLaser: null,
    carriedPartMesh: null,
    floorPartMesh: null,
    deliveredPartMesh: null,
    waypointGroups: [],
    trailLine: null,
    sparkPoints: null,
    sparkVel: [],
    sparksActive: false,
    shockwaveRing: null,
    shockwaveScale: 0,
    obstacleGroups: [],
    interactiveMeshes: [],
    dragTarget: null,
    raycaster: null,
    floorPlane: null,
    pointerNdc: null,
    floorHitVec: null,
    textures: {}
  };

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function isDarkTheme() {
    const attr = document.documentElement.getAttribute("data-theme");
    if (attr === "dark") return true;
    if (attr === "light") return false;
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  }

  function to3D(px, py) {
    return { x: (px - BASE_2D[0]) / SCALE, z: (py - BASE_2D[1]) / SCALE };
  }

  function to2D(x3, z3) {
    return { x: x3 * SCALE + BASE_2D[0], y: z3 * SCALE + BASE_2D[1] };
  }

  function isBrazoSectionActive() {
    const sec = document.getElementById("sectionBrazo");
    return !sec || sec.classList.contains("active");
  }

  function isAnyModalOpen() {
    return Boolean(document.querySelector(".modal-backdrop.open, .lightbox-backdrop.open"));
  }

  function shouldRunRenderLoop() {
    return three.ready && isBrazoSectionActive() && !document.hidden && !isAnyModalOpen();
  }

  function stopRenderLoop() {
    if (state.rafId !== null) {
      cancelAnimationFrame(state.rafId);
      state.rafId = null;
    }
  }

  function ensureRenderLoop() {
    if (!shouldRunRenderLoop()) {
      stopRenderLoop();
      return;
    }
    if (state.rafId === null) {
      state.lastTickTime = performance.now();
      startRenderLoop();
    }
  }

  function resizeThreeRenderer() {
    if (!three.renderer || !three.camera || !el.container3d) return;
    const nw = el.container3d.clientWidth;
    const nh = el.container3d.clientHeight;
    if (nw > 10 && nh > 10) {
      three.camera.aspect = nw / nh;
      three.camera.updateProjectionMatrix();
      three.renderer.setSize(nw, nh);
    }
  }

  function loadThreeLibrary() {
    if (typeof window.THREE !== "undefined") return Promise.resolve(window.THREE);
    if (threeLoadPromise) return threeLoadPromise;

    threeLoadPromise = new Promise((resolve, reject) => {
      const existing = document.querySelector(`script[src="${THREE_CDN_URL}"]`);
      if (existing) {
        existing.addEventListener("load", () => resolve(window.THREE), { once: true });
        existing.addEventListener("error", () => reject(new Error("Three.js load failed")), { once: true });
        return;
      }
      const script = document.createElement("script");
      script.src = THREE_CDN_URL;
      script.async = true;
      script.onload = () => (window.THREE ? resolve(window.THREE) : reject(new Error("Three.js missing")));
      script.onerror = () => reject(new Error("Three.js load failed"));
      document.head.appendChild(script);
    });
    return threeLoadPromise;
  }

  async function ensureBrazoActivated() {
    if (!state.meta) return;
    bindUiEvents();

    if (!state.activated) {
      state.activated = true;
      let loadingBanner = null;
      if (!three.ready && typeof window.THREE === "undefined" && el.container3d) {
        loadingBanner = document.createElement("div");
        loadingBanner.className = "arm-3d-loading";
        loadingBanner.textContent = "Cargando escena 3D...";
        el.container3d.appendChild(loadingBanner);
      }

      try {
        await loadThreeLibrary();
      } catch (err) {
        // Continua funcionando el mapa C-Space y modales incluso sin WebGL/CDN
      } finally {
        if (loadingBanner) loadingBanner.remove();
      }

      if (!three.ready) {
        initThreeScene();
        bindThreePointerEvents();
      }
      requestAnimationFrame(() => {
        resizeThreeRenderer();
        ensureRenderLoop();
      });
      await runPythonSequence();
    } else {
      resizeThreeRenderer();
      ensureRenderLoop();
    }
  }

  async function init() {
    try {
      const resp = await fetch("/api/arm/presets");
      const json = await resp.json();
      if (json.status !== "success") return;

      state.meta = json.data;
      renderPresetButtons();
      loadTask("pick_and_place", false);
      refreshHistoryBadge();

      const sec = document.getElementById("sectionBrazo");
      if (isBrazoSectionActive()) {
        await ensureBrazoActivated();
      } else if (sec && typeof MutationObserver !== "undefined") {
        const obs = new MutationObserver(() => {
          if (isBrazoSectionActive()) {
            ensureBrazoActivated();
          } else {
            stopRenderLoop();
          }
        });
        obs.observe(sec, { attributes: true, attributeFilter: ["class"] });
      } else {
        await ensureBrazoActivated();
      }
    } catch (err) {
      el.verdictText.textContent = "Error al conectar con el backend Python.";
    }
  }

  function renderPresetButtons() {
    el.presetButtons.innerHTML = state.meta.tasks
      .map((t) => {
        const active = t.id === state.activeTaskId ? "active" : "";
        return `<button type="button" class="arm-preset-btn ${active}" data-task="${escapeHtml(t.id)}" title="${escapeHtml(t.subtitle)}">${escapeHtml(t.name)}</button>`;
      })
      .join("");

    el.presetButtons.querySelectorAll(".arm-preset-btn").forEach((btn) => {
      btn.addEventListener("click", () => loadTask(btn.dataset.task, true));
    });
  }

  function getActiveCargoSpec() {
    const list = (state.meta && state.meta.cargos) || [];
    return (
      list.find((c) => c.id === state.cargoId) || {
        id: "battery_module",
        name: "Modulo Bateria EV",
        short_name: "Bateria EV",
        weight_kg: 18.0,
        torque_tax_factor: 0.35,
        color_hex: "#38bdf8"
      }
    );
  }

  function loadTask(taskId, solveNow = true) {
    const task = state.meta.tasks.find((t) => t.id === taskId) || state.meta.tasks[0];
    state.activeTaskId = task.id;
    state.cargoId = task.default_cargo || "battery_module";
    if (el.cargoSelect) el.cargoSelect.value = state.cargoId;
    state.startDeg = [...task.start_deg];
    state.liveDeg = [...task.start_deg];
    state.waypoints = task.waypoints.map((w) => ({ ...w }));
    state.obstacles = task.obstacles.map((o) => ({ ...o }));
    state.unexpectedSpec = task.unexpected ? { ...task.unexpected } : null;
    state.unexpectedActive = false;
    state.carryingPart = false;
    state.deliveredPart = false;
    state.completedWaypoints = 0;

    el.btnEmergency.classList.remove("active");
    el.btnEmergency.textContent = "Imprevisto";
    el.presetButtons.querySelectorAll(".arm-preset-btn").forEach((b) => {
      b.classList.toggle("active", b.dataset.task === task.id);
    });

    if (three.ready) {
      refreshCarriedCargoMesh();
      rebuildThreeObstaclesAndWaypoints();
    }
    if (solveNow) runPythonSequence();
  }

  // =========================================================================
  // TEXTURAS PROCEDURALES
  // =========================================================================
  function createStripeTexture(colorA, colorB) {
    const THREE = window.THREE;
    const c = document.createElement("canvas");
    c.width = 64;
    c.height = 64;
    const ctx = c.getContext("2d");
    ctx.fillStyle = colorA;
    ctx.fillRect(0, 0, 64, 64);
    ctx.fillStyle = colorB;
    ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(32, 0); ctx.lineTo(0, 32); ctx.closePath(); ctx.fill();
    ctx.beginPath(); ctx.moveTo(64, 0); ctx.lineTo(64, 32); ctx.lineTo(32, 64); ctx.lineTo(0, 64); ctx.closePath(); ctx.fill();
    const tex = new THREE.CanvasTexture(c);
    tex.wrapS = THREE.RepeatWrapping;
    tex.wrapT = THREE.RepeatWrapping;
    tex.repeat.set(3, 1);
    return tex;
  }

  function createFloorTexture(dark) {
    const THREE = window.THREE;
    const c = document.createElement("canvas");
    c.width = 512;
    c.height = 512;
    const ctx = c.getContext("2d");
    ctx.fillStyle = dark ? "#1A242E" : "#D6DDD6";
    ctx.fillRect(0, 0, 512, 512);

    ctx.strokeStyle = dark ? "rgba(143,196,182,0.08)" : "rgba(30,42,51,0.08)";
    ctx.lineWidth = 1;
    for (let i = 0; i <= 512; i += 32) {
      ctx.beginPath(); ctx.moveTo(i, 0); ctx.lineTo(i, 512); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(0, i); ctx.lineTo(512, i); ctx.stroke();
    }
    ctx.strokeStyle = dark ? "rgba(143,196,182,0.16)" : "rgba(30,42,51,0.15)";
    ctx.lineWidth = 2;
    for (let i = 0; i <= 512; i += 128) {
      ctx.beginPath(); ctx.moveTo(i, 0); ctx.lineTo(i, 512); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(0, i); ctx.lineTo(512, i); ctx.stroke();
    }
    const tex = new THREE.CanvasTexture(c);
    tex.wrapS = THREE.RepeatWrapping;
    tex.wrapT = THREE.RepeatWrapping;
    tex.repeat.set(3, 3);
    return tex;
  }

  function disposeObject3D(obj) {
    if (!obj) return;
    const sharedTex = new Set(Object.values(three.textures));
    obj.traverse((child) => {
      if (child.geometry && typeof child.geometry.dispose === "function") {
        child.geometry.dispose();
      }
      if (child.material) {
        const mats = Array.isArray(child.material) ? child.material : [child.material];
        mats.forEach((m) => {
          if (m.map && !sharedTex.has(m.map) && typeof m.map.dispose === "function") {
            m.map.dispose();
          }
          if (typeof m.dispose === "function") {
            m.dispose();
          }
        });
      }
    });
  }

  // =========================================================================
  // ESCENA 3D EN THREE.JS
  // =========================================================================
  function initThreeScene() {
    if (typeof window.THREE === "undefined") {
      if (el.container3d && !el.container3d.querySelector(".arm-3d-loading")) {
        const msg = document.createElement("div");
        msg.className = "arm-3d-loading";
        msg.textContent = "Vista 3D no disponible sin conexion a Three.js. El Mapa de Decisiones y la Bitacora SQL siguen activos.";
        el.container3d.appendChild(msg);
      }
      return;
    }

    const THREE = window.THREE;
    const w = el.container3d.clientWidth || 560;
    const h = el.container3d.clientHeight || 400;

    three.scene = new THREE.Scene();
    three.textures.hazardYellow = createStripeTexture("#D97706", "#1E293B");
    three.textures.hazardRed = createStripeTexture("#B91C1C", "#F8FAFC");
    three.textures.floorDark = createFloorTexture(true);
    three.textures.floorLight = createFloorTexture(false);

    three.camera = new THREE.PerspectiveCamera(40, w / h, 0.1, 100);
    updateCameraPosition();

    three.renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
    three.renderer.setSize(w, h);
    three.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    three.renderer.shadowMap.enabled = true;
    three.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    three.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    three.renderer.toneMappingExposure = 1.08;

    const existingCanvas = el.container3d.querySelector("canvas");
    if (existingCanvas) existingCanvas.remove();
    el.container3d.insertBefore(three.renderer.domElement, el.container3d.firstChild);

    three.raycaster = new THREE.Raycaster();
    three.floorPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
    three.pointerNdc = new THREE.Vector2();
    three.floorHitVec = new THREE.Vector3();

    const hemi = new THREE.HemisphereLight(0xf8fafc, 0x26323d, 0.92);
    three.scene.add(hemi);

    const keyLight = new THREE.DirectionalLight(0xfffbeb, 1.45);
    keyLight.position.set(6, 13, 8);
    keyLight.castShadow = true;
    keyLight.shadow.mapSize.set(1024, 1024);
    keyLight.shadow.bias = -0.0005;
    const d = 9.5;
    keyLight.shadow.camera.left = -d;
    keyLight.shadow.camera.right = d;
    keyLight.shadow.camera.top = d;
    keyLight.shadow.camera.bottom = -d;
    three.scene.add(keyLight);

    const rimLight = new THREE.DirectionalLight(0x5fb3a2, 0.7);
    rimLight.position.set(-7, 6, -6);
    three.scene.add(rimLight);

    const fillLight = new THREE.PointLight(0xe0f2fe, 0.55, 22);
    fillLight.position.set(0, 6.5, 2.5);
    three.scene.add(fillLight);

    const floorMat = new THREE.MeshStandardMaterial({
      map: isDarkTheme() ? three.textures.floorDark : three.textures.floorLight,
      roughness: 0.68,
      metalness: 0.14
    });
    const floor = new THREE.Mesh(new THREE.PlaneGeometry(24, 24), floorMat);
    floor.rotation.x = -Math.PI / 2;
    floor.receiveShadow = true;
    three.scene.add(floor);
    three.floorMesh = floor;

    updateSceneTheme();

    // Zona de alcance y perimetro industrial de la celda
    const reach = L1_3D + L2_3D;
    const reachRing = new THREE.Mesh(
      new THREE.RingGeometry(reach - 0.055, reach + 0.055, 72),
      new THREE.MeshBasicMaterial({ color: 0x4f8c82, side: THREE.DoubleSide, transparent: true, opacity: 0.52 })
    );
    reachRing.rotation.x = -Math.PI / 2;
    reachRing.position.y = 0.015;
    three.scene.add(reachRing);

    const innerRing = new THREE.Mesh(
      new THREE.RingGeometry(L1_3D - 0.025, L1_3D + 0.025, 64),
      new THREE.MeshBasicMaterial({ color: 0x64748b, side: THREE.DoubleSide, transparent: true, opacity: 0.25 })
    );
    innerRing.rotation.x = -Math.PI / 2;
    innerRing.position.y = 0.014;
    three.scene.add(innerRing);

    buildIndustrialBayFrame();
    buildThreeRobot();
    buildThreeGhostRobot();
    buildThreeEffects();
    rebuildThreeObstaclesAndWaypoints();

    if (typeof ResizeObserver !== "undefined") {
      const ro = new ResizeObserver(resizeThreeRenderer);
      ro.observe(el.container3d);
    }

    three.ready = true;
    ensureRenderLoop();
  }

  function updateSceneTheme() {
    if (!three.scene || !window.THREE) return;
    const dark = isDarkTheme();
    const bgHex = dark ? 0x131b22 : 0xdfe5de;
    three.scene.background = new window.THREE.Color(bgHex);
    three.scene.fog = new window.THREE.Fog(bgHex, 14, 28);
    if (three.floorMesh) {
      three.floorMesh.material.map = dark ? three.textures.floorDark : three.textures.floorLight;
      three.floorMesh.material.needsUpdate = true;
    }
  }

  function updateCameraPosition() {
    if (!three.camera) return;
    const x = three.camRadius * Math.sin(three.camPhi) * Math.sin(three.camTheta);
    const y = three.camRadius * Math.cos(three.camPhi);
    const z = three.camRadius * Math.sin(three.camPhi) * Math.cos(three.camTheta);
    three.camera.position.set(x, Math.max(2.2, y), z);
    three.camera.lookAt(0.45, 0.45, 0);
  }

  function buildIndustrialBayFrame() {
    const THREE = window.THREE;
    const postMat = new THREE.MeshStandardMaterial({ color: 0x334155, metalness: 0.65, roughness: 0.35 });
    const hazardMat = new THREE.MeshStandardMaterial({ map: three.textures.hazardYellow, roughness: 0.55 });
    const railMat = new THREE.MeshStandardMaterial({ color: 0xd97706, metalness: 0.45, roughness: 0.4 });

    const corners = [[-5.7, -4.5], [5.7, -4.5], [-5.7, 4.5], [5.7, 4.5]];
    corners.forEach(([cx, cz]) => {
      const collar = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.17, 0.18, 12), hazardMat);
      collar.position.set(cx, 0.09, cz);
      collar.castShadow = true;
      three.scene.add(collar);

      const post = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 0.92, 12), postMat);
      post.position.set(cx, 0.54, cz);
      post.castShadow = true;
      three.scene.add(post);

      const cap = new THREE.Mesh(new THREE.SphereGeometry(0.085, 12, 12), railMat);
      cap.position.set(cx, 1.0, cz);
      three.scene.add(cap);
    });

    // Barandal trasero ligero para enmarcar la celda sin tapar la vista frontal
    [0.45, 0.85].forEach((ry) => {
      const rail = new THREE.Mesh(new THREE.CylinderGeometry(0.032, 0.032, 11.4, 10), railMat);
      rail.rotation.z = Math.PI / 2;
      rail.position.set(0, ry, -4.5);
      three.scene.add(rail);
    });

    // Marcas perimetrales de piso
    const lineMat = new THREE.MeshBasicMaterial({ color: 0xd97706, transparent: true, opacity: 0.36 });
    const backLine = new THREE.Mesh(new THREE.PlaneGeometry(11.4, 0.08), lineMat);
    backLine.rotation.x = -Math.PI / 2;
    backLine.position.set(0, 0.012, -4.5);
    three.scene.add(backLine);

    const frontLine = new THREE.Mesh(new THREE.PlaneGeometry(11.4, 0.08), lineMat);
    frontLine.rotation.x = -Math.PI / 2;
    frontLine.position.set(0, 0.012, 4.5);
    three.scene.add(frontLine);
  }

  function buildThreeRobot() {
    const THREE = window.THREE;
    const armY = 1.12;
    const steelDark = new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.36, metalness: 0.78 });
    const steelMid = new THREE.MeshStandardMaterial({ color: 0x475569, roughness: 0.35, metalness: 0.7 });
    const chromeMat = new THREE.MeshStandardMaterial({ color: 0xcbd5e1, roughness: 0.2, metalness: 0.9 });
    const tealMat = new THREE.MeshStandardMaterial({ color: 0x2a7b6f, roughness: 0.28, metalness: 0.55 });
    const goldMat = new THREE.MeshStandardMaterial({ color: 0xd4943a, roughness: 0.28, metalness: 0.55 });

    // Base octagonal robusta con pernos y aletas de refrigeracion
    const basePlate = new THREE.Mesh(new THREE.CylinderGeometry(0.84, 0.92, 0.12, 8), steelDark);
    basePlate.position.y = 0.06;
    basePlate.receiveShadow = true;
    basePlate.castShadow = true;
    three.scene.add(basePlate);

    const baseFlange = new THREE.Mesh(new THREE.CylinderGeometry(0.68, 0.74, 0.08, 24), steelMid);
    baseFlange.position.y = 0.14;
    three.scene.add(baseFlange);

    for (let b = 0; b < 8; b++) {
      const ang = (b * Math.PI) / 4;
      const bolt = new THREE.Mesh(new THREE.CylinderGeometry(0.048, 0.048, 0.07, 6), chromeMat);
      bolt.position.set(Math.cos(ang) * 0.76, 0.13, Math.sin(ang) * 0.76);
      three.scene.add(bolt);
    }

    const pedestal = new THREE.Mesh(new THREE.CylinderGeometry(0.42, 0.58, armY - 0.14, 28), steelDark);
    pedestal.position.y = 0.14 + (armY - 0.14) / 2;
    pedestal.castShadow = true;
    three.scene.add(pedestal);

    // Anillo LED de estado del robot (cambia de color segun fase: explorando, transportando, listo, fallo)
    three.statusRing = new THREE.Mesh(
      new THREE.TorusGeometry(0.48, 0.036, 12, 36),
      new THREE.MeshBasicMaterial({ color: 0x4fd1c5 })
    );
    three.statusRing.rotation.x = Math.PI / 2;
    three.statusRing.position.y = 0.26;
    three.scene.add(three.statusRing);

    const upperCollar = new THREE.Mesh(new THREE.TorusGeometry(0.43, 0.025, 10, 32), chromeMat);
    upperCollar.rotation.x = Math.PI / 2;
    upperCollar.position.y = armY - 0.18;
    three.scene.add(upperCollar);

    three.shoulderGroup = new THREE.Group();
    three.shoulderGroup.position.set(0, armY, 0);
    three.scene.add(three.shoulderGroup);

    // Articulacion de hombro con tambor de servomotor y contrapeso trasero
    const shHousing = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.38, 0.44, 24), steelDark);
    shHousing.castShadow = true;
    three.shoulderGroup.add(shHousing);
    three.shoulderGroup.add(new THREE.Mesh(new THREE.CylinderGeometry(0.24, 0.24, 0.48, 20), chromeMat));

    const counterweight = new THREE.Mesh(new THREE.BoxGeometry(0.42, 0.26, 0.34), steelMid);
    counterweight.position.set(-0.34, 0.02, 0);
    counterweight.castShadow = true;
    three.shoulderGroup.add(counterweight);

    // Eslabon 1 (estructura doble con rieles metalicos y conducto de cables)
    const link1Body = new THREE.Mesh(new THREE.BoxGeometry(L1_3D, 0.24, 0.34), tealMat);
    link1Body.position.x = L1_3D / 2;
    link1Body.castShadow = true;
    three.shoulderGroup.add(link1Body);

    const link1Rail = new THREE.Mesh(new THREE.BoxGeometry(L1_3D * 0.82, 0.06, 0.38), chromeMat);
    link1Rail.position.set(L1_3D / 2, 0.11, 0);
    three.shoulderGroup.add(link1Rail);

    const cableCurve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(0.15, 0.22, 0.18),
      new THREE.Vector3(L1_3D * 0.5, 0.38, 0.21),
      new THREE.Vector3(L1_3D - 0.1, 0.26, 0.16)
    ]);
    const cableMesh = new THREE.Mesh(
      new THREE.TubeGeometry(cableCurve, 16, 0.032, 8, false),
      steelDark
    );
    three.shoulderGroup.add(cableMesh);

    three.elbowGroup = new THREE.Group();
    three.elbowGroup.position.set(L1_3D, 0.18, 0);
    three.shoulderGroup.add(three.elbowGroup);

    const elHousing = new THREE.Mesh(new THREE.CylinderGeometry(0.27, 0.28, 0.38, 24), steelDark);
    elHousing.castShadow = true;
    three.elbowGroup.add(elHousing);
    three.elbowGroup.add(new THREE.Mesh(new THREE.CylinderGeometry(0.17, 0.17, 0.43, 18), chromeMat));

    const link2Body = new THREE.Mesh(new THREE.BoxGeometry(L2_3D, 0.19, 0.26), goldMat);
    link2Body.position.x = L2_3D / 2;
    link2Body.castShadow = true;
    three.elbowGroup.add(link2Body);

    const link2Rail = new THREE.Mesh(new THREE.BoxGeometry(L2_3D * 0.78, 0.045, 0.29), chromeMat);
    link2Rail.position.set(L2_3D / 2, 0.09, 0);
    three.elbowGroup.add(link2Rail);

    // Actuador vertical Z con doble varilla cromada
    const torchCollar = new THREE.Mesh(new THREE.CylinderGeometry(0.15, 0.13, 0.30, 16), steelDark);
    torchCollar.position.set(L2_3D, -0.05, 0);
    three.elbowGroup.add(torchCollar);

    const torchNozzle = new THREE.Mesh(new THREE.CylinderGeometry(0.068, 0.042, 0.48, 16), chromeMat);
    torchNozzle.position.set(L2_3D, -0.38, 0);
    torchNozzle.castShadow = true;
    three.elbowGroup.add(torchNozzle);

    [-0.08, 0.08].forEach((rz) => {
      const rod = new THREE.Mesh(new THREE.CylinderGeometry(0.022, 0.022, 0.46, 8), steelMid);
      rod.position.set(L2_3D, -0.38, rz);
      three.elbowGroup.add(rod);
    });

    const copperTip = new THREE.Mesh(
      new THREE.SphereGeometry(0.06, 14, 14),
      new THREE.MeshBasicMaterial({ color: 0xfbbf24 })
    );
    copperTip.position.set(L2_3D, -0.64, 0);
    three.elbowGroup.add(copperTip);

    // Pinza mecanica paralela (mordazas calibradas debajo de la barra sin interpenetracion)
    const jawMat = new THREE.MeshStandardMaterial({ color: 0xe2e8f0, metalness: 0.85, roughness: 0.22 });
    const jawBar = new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.06, 0.62), steelDark);
    jawBar.position.set(L2_3D, -0.73, 0);
    three.elbowGroup.add(jawBar);

    three.gripperLeft = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.36, 0.065), jawMat);
    three.gripperLeft.position.set(L2_3D, -0.95, 0.28);
    three.gripperLeft.castShadow = true;
    three.elbowGroup.add(three.gripperLeft);

    three.gripperRight = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.36, 0.065), jawMat);
    three.gripperRight.position.set(L2_3D, -0.95, -0.28);
    three.gripperRight.castShadow = true;
    three.elbowGroup.add(three.gripperRight);

    three.clampHalo = new THREE.Mesh(
      new THREE.TorusGeometry(0.36, 0.024, 12, 32),
      new THREE.MeshBasicMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.85 })
    );
    three.clampHalo.rotation.x = Math.PI / 2;
    three.clampHalo.position.set(L2_3D, -0.91, 0);
    three.clampHalo.visible = false;
    three.elbowGroup.add(three.clampHalo);

    three.cargoLaser = new THREE.Mesh(
      new THREE.CylinderGeometry(0.035, 0.11, 0.22, 16, 1, true),
      new THREE.MeshBasicMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.20, side: THREE.DoubleSide })
    );
    three.cargoLaser.position.set(L2_3D, -0.95, 0);
    three.cargoLaser.visible = false;
    three.elbowGroup.add(three.cargoLaser);

    // Grupo 3D de la carga sujetada entre ambas mordazas sin tocar la barra superior
    three.carriedPartMesh = new THREE.Group();
    three.carriedPartMesh.position.set(L2_3D, -1.03, 0);
    three.carriedPartMesh.scale.set(0.84, 0.84, 0.84);
    three.carriedPartMesh.visible = false;
    three.elbowGroup.add(three.carriedPartMesh);
    refreshCarriedCargoMesh();

    three.torchLight = new THREE.PointLight(0xfbbf24, 0.0, 4.5);
    three.torchLight.position.set(L2_3D, -1.0, 0);
    three.elbowGroup.add(three.torchLight);
  }

  function populateCargoMeshGroup(targetGroup, cargoId) {
    if (!targetGroup || !window.THREE) return;
    const THREE = window.THREE;
    while (targetGroup.children.length > 0) {
      const child = targetGroup.children[0];
      targetGroup.remove(child);
      disposeObject3D(child);
    }

    if (cargoId === "door_panel") {
      // Bastidor de Puerta (12 kg): estructura dorada/acero con travesanos
      const frameMat = new THREE.MeshStandardMaterial({ color: 0xf59e0b, metalness: 0.68, roughness: 0.26, emissive: 0xb45309, emissiveIntensity: 0.25 });
      const steelMat = new THREE.MeshStandardMaterial({ color: 0xcbd5e1, metalness: 0.85, roughness: 0.2 });

      const base = new THREE.Mesh(new THREE.BoxGeometry(0.62, 0.14, 0.48), frameMat);
      base.castShadow = true;
      targetGroup.add(base);

      const arch = new THREE.Mesh(new THREE.BoxGeometry(0.46, 0.16, 0.32), steelMat);
      arch.position.y = 0.14;
      arch.castShadow = true;
      targetGroup.add(arch);

      const handle = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.36, 12), frameMat);
      handle.rotation.z = Math.PI / 2;
      handle.position.y = 0.24;
      targetGroup.add(handle);
    } else if (cargoId === "ecu_sensor") {
      // Modulo LiDAR / ECU (5 kg): chasis esmeralda con domo optico brillante
      const bodyMat = new THREE.MeshStandardMaterial({ color: 0x10b981, metalness: 0.62, roughness: 0.28, emissive: 0x047857, emissiveIntensity: 0.3 });
      const domeMat = new THREE.MeshStandardMaterial({ color: 0x38bdf8, metalness: 0.9, roughness: 0.1, emissive: 0x0284c7, emissiveIntensity: 0.45 });

      const base = new THREE.Mesh(new THREE.CylinderGeometry(0.28, 0.32, 0.18, 20), bodyMat);
      base.castShadow = true;
      targetGroup.add(base);

      const dome = new THREE.Mesh(new THREE.CylinderGeometry(0.17, 0.20, 0.14, 20), domeMat);
      dome.position.y = 0.15;
      dome.castShadow = true;
      targetGroup.add(dome);
    } else {
      // Modulo Bateria EV (18 kg): carcasa azul cobalto con 4 celdas de litio y barra colectora
      const packMat = new THREE.MeshStandardMaterial({ color: 0x0284c7, metalness: 0.72, roughness: 0.24, emissive: 0x0369a1, emissiveIntensity: 0.32 });
      const cellMat = new THREE.MeshStandardMaterial({ color: 0xe2e8f0, metalness: 0.88, roughness: 0.18 });
      const busMat = new THREE.MeshBasicMaterial({ color: 0xf97316 });

      const casing = new THREE.Mesh(new THREE.BoxGeometry(0.58, 0.22, 0.54), packMat);
      casing.castShadow = true;
      targetGroup.add(casing);

      const offsets = [[-0.14, -0.13], [0.14, -0.13], [-0.14, 0.13], [0.14, 0.13]];
      offsets.forEach(([ox, oz]) => {
        const cell = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 0.12, 14), cellMat);
        cell.position.set(ox, 0.15, oz);
        cell.castShadow = true;
        targetGroup.add(cell);
      });

      const busbar = new THREE.Mesh(new THREE.BoxGeometry(0.42, 0.04, 0.10), busMat);
      busbar.position.y = 0.22;
      targetGroup.add(busbar);
    }
  }

  function refreshCarriedCargoMesh() {
    if (!three.carriedPartMesh) return;
    populateCargoMeshGroup(three.carriedPartMesh, state.cargoId);
  }

  function buildThreeGhostRobot() {
    const THREE = window.THREE;
    three.ghostMat = new THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      transparent: true,
      opacity: 0.34
    });

    three.ghostShoulder = new THREE.Group();
    three.ghostShoulder.position.set(0, 1.12, 0);
    three.ghostShoulder.visible = false;
    three.scene.add(three.ghostShoulder);

    const g1 = new THREE.Mesh(new THREE.BoxGeometry(L1_3D, 0.18, 0.22), three.ghostMat);
    g1.position.x = L1_3D / 2;
    three.ghostShoulder.add(g1);

    three.ghostElbow = new THREE.Group();
    three.ghostElbow.position.set(L1_3D, 0.18, 0);
    three.ghostShoulder.add(three.ghostElbow);

    const g2 = new THREE.Mesh(new THREE.BoxGeometry(L2_3D, 0.14, 0.18), three.ghostMat);
    g2.position.x = L2_3D / 2;
    three.ghostElbow.add(g2);
  }

  function buildThreeEffects() {
    const THREE = window.THREE;
    const count = 42;
    const positions = new Float32Array(count * 3);
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    three.sparkPoints = new THREE.Points(
      geo,
      new THREE.PointsMaterial({ color: 0xfde047, size: 0.17, transparent: true, opacity: 0.95 })
    );
    three.sparkPoints.visible = false;
    three.scene.add(three.sparkPoints);

    for (let i = 0; i < count; i++) three.sparkVel.push({ vx: 0, vy: 0, vz: 0 });

    three.shockwaveRing = new THREE.Mesh(
      new THREE.RingGeometry(0.18, 0.26, 36),
      new THREE.MeshBasicMaterial({ color: 0xfbbf24, side: THREE.DoubleSide, transparent: true, opacity: 0.8 })
    );
    three.shockwaveRing.rotation.x = -Math.PI / 2;
    three.shockwaveRing.position.y = 0.04;
    three.shockwaveRing.visible = false;
    three.scene.add(three.shockwaveRing);
  }

  function triggerSparks(x, z, colorHex = 0xfbbf24) {
    if (!three.sparkPoints) return;
    const pos = three.sparkPoints.geometry.attributes.position.array;
    for (let i = 0; i < three.sparkVel.length; i++) {
      pos[i * 3] = x;
      pos[i * 3 + 1] = 0.34;
      pos[i * 3 + 2] = z;
      const ang = Math.random() * Math.PI * 2;
      const spd = 0.03 + Math.random() * 0.085;
      three.sparkVel[i] = {
        vx: Math.cos(ang) * spd,
        vy: 0.05 + Math.random() * 0.10,
        vz: Math.sin(ang) * spd
      };
    }
    three.sparkPoints.material.color.setHex(colorHex);
    three.sparkPoints.geometry.attributes.position.needsUpdate = true;
    three.sparkPoints.visible = true;
    three.sparksActive = true;

    if (three.shockwaveRing) {
      three.shockwaveRing.material.color.setHex(colorHex);
      three.shockwaveRing.position.set(x, 0.04, z);
      three.shockwaveRing.scale.set(1, 1, 1);
      three.shockwaveRing.material.opacity = 0.9;
      three.shockwaveRing.visible = true;
      three.shockwaveScale = 1.0;
    }
    if (three.torchLight) {
      three.torchLight.color.setHex(colorHex);
      three.torchLight.intensity = 3.2;
    }
  }

  function createStationBadgeSprite(text, bgHex) {
    const THREE = window.THREE;
    const texKey = `badge_${text}`;
    let tex = three.textures[texKey];
    if (!tex) {
      const canvas = document.createElement("canvas");
      canvas.width = 256;
      canvas.height = 72;
      const ctx = canvas.getContext("2d");

      ctx.fillStyle = bgHex;
      ctx.beginPath();
      if (typeof ctx.roundRect === "function") {
        ctx.roundRect(12, 10, 232, 52, 26);
      } else {
        ctx.rect(12, 10, 232, 52);
      }
      ctx.fill();

      ctx.strokeStyle = "rgba(255,255,255,0.65)";
      ctx.lineWidth = 4;
      ctx.stroke();

      ctx.fillStyle = "#ffffff";
      ctx.font = "700 28px 'IBM Plex Sans', sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(text, 128, 37);

      tex = new THREE.CanvasTexture(canvas);
      three.textures[texKey] = tex;
    }

    const mat = new THREE.SpriteMaterial({ map: tex, transparent: true, depthTest: true });
    const sprite = new THREE.Sprite(mat);
    sprite.scale.set(0.96, 0.27, 1);
    return sprite;
  }

  function updateTrail3D(frames, isCarrying = false) {
    const THREE = window.THREE;
    if (three.trailLine) {
      three.scene.remove(three.trailLine);
      if (three.trailLine.geometry) three.trailLine.geometry.dispose();
      if (three.trailLine.material) three.trailLine.material.dispose();
      three.trailLine = null;
    }
    if (!frames || frames.length < 2) return;

    const pts = [];
    for (let i = 0; i < frames.length; i++) {
      const p3 = to3D(frames[i].tx, frames[i].ty);
      const v = new THREE.Vector3(p3.x, 0.34, p3.z);
      if (!pts.length || pts[pts.length - 1].distanceToSquared(v) > 0.0004) {
        pts.push(v);
      }
    }
    if (pts.length < 2) return;

    const colorHex = isCarrying ? 0x38bdf8 : 0xe0ae63;
    const curve = new THREE.CatmullRomCurve3(pts);
    const segs = Math.min(96, Math.max(12, pts.length * 2));
    const geo = new THREE.TubeGeometry(curve, segs, 0.036, 8, false);
    three.trailLine = new THREE.Mesh(
      geo,
      new THREE.MeshBasicMaterial({
        color: colorHex,
        transparent: true,
        opacity: 0.88
      })
    );
    three.scene.add(three.trailLine);
  }

  function createObstacleGroup(ob, idx) {
    const THREE = window.THREE;
    const w3 = ob.w / SCALE;
    const d3 = ob.h / SCALE;
    const pos3 = to3D(ob.x + ob.w / 2, ob.y + ob.h / 2);

    const group = new THREE.Group();
    group.position.set(pos3.x, 0, pos3.z);

    const addPart = (mesh) => {
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      mesh.userData = { dragType: "obstacle", index: idx, label: ob.label, parentGroup: group };
      group.add(mesh);
      return mesh;
    };

    if (ob.kind === "car_body") {
      // Carroceria automotriz sobre bancada de ensamble con cabina y ventanillas
      const jigMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.75, roughness: 0.35 });
      const paintMat = new THREE.MeshStandardMaterial({ color: 0x336699, metalness: 0.62, roughness: 0.24 });
      const glassMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, metalness: 0.9, roughness: 0.12 });
      const trimMat = new THREE.MeshStandardMaterial({ color: 0xcbd5e1, metalness: 0.85, roughness: 0.2 });

      const leg = new THREE.Mesh(new THREE.BoxGeometry(w3 * 0.86, 0.26, d3 * 0.78), jigMat);
      leg.position.y = 0.13;
      addPart(leg);

      const lowerBody = new THREE.Mesh(new THREE.BoxGeometry(w3, 0.56, d3), paintMat);
      lowerBody.position.y = 0.54;
      addPart(lowerBody);

      const cabin = new THREE.Mesh(new THREE.BoxGeometry(w3 * 0.68, 0.38, d3 * 0.9), paintMat);
      cabin.position.y = 0.98;
      addPart(cabin);

      const win = new THREE.Mesh(new THREE.BoxGeometry(w3 * 0.62, 0.28, d3 * 0.93), glassMat);
      win.position.y = 0.99;
      addPart(win);

      const trim = new THREE.Mesh(new THREE.BoxGeometry(w3 * 1.01, 0.05, d3 * 1.01), trimMat);
      trim.position.y = 0.55;
      addPart(trim);
    } else if (ob.kind === "press") {
      const isEmergency = ob.id === "obs_emergency";
      const base = new THREE.Mesh(
        new THREE.BoxGeometry(w3, 0.24, d3),
        new THREE.MeshStandardMaterial({ map: isEmergency ? three.textures.hazardRed : three.textures.hazardYellow, roughness: 0.58 })
      );
      base.position.y = 0.12;
      addPart(base);

      if (isEmergency) {
        const crate = new THREE.Mesh(
          new THREE.BoxGeometry(w3 * 0.92, 0.78, d3 * 0.92),
          new THREE.MeshStandardMaterial({ color: 0xdc2626, roughness: 0.38, metalness: 0.4 })
        );
        crate.position.y = 0.63;
        addPart(crate);

        const beacon = new THREE.Mesh(
          new THREE.CylinderGeometry(0.11, 0.13, 0.20, 16),
          new THREE.MeshStandardMaterial({ color: 0xef4444, emissive: 0xef4444, emissiveIntensity: 0.9 })
        );
        beacon.position.y = 1.12;
        addPart(beacon);
        three.emergencyBeacons.push(beacon);
      } else {
        const frameMat = new THREE.MeshStandardMaterial({ color: 0xd97706, roughness: 0.38, metalness: 0.42 });
        const steelMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.4, metalness: 0.7 });
        const pistonMat = new THREE.MeshStandardMaterial({ color: 0xcbd5e1, roughness: 0.2, metalness: 0.9 });

        [-w3 * 0.36, w3 * 0.36].forEach((px) => {
          const pillar = new THREE.Mesh(new THREE.BoxGeometry(w3 * 0.22, 1.30, d3 * 0.86), frameMat);
          pillar.position.set(px, 0.89, 0);
          addPart(pillar);
        });

        const ram = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.16, 0.72, 16), pistonMat);
        ram.position.y = 1.06;
        addPart(ram);

        const dieHead = new THREE.Mesh(new THREE.BoxGeometry(w3 * 0.46, 0.22, d3 * 0.64), steelMat);
        dieHead.position.y = 0.66;
        addPart(dieHead);

        const crown = new THREE.Mesh(new THREE.BoxGeometry(w3 * 0.98, 0.32, d3 * 0.92), steelMat);
        crown.position.y = 1.66;
        addPart(crown);
      }
    } else if (ob.kind === "pillar") {
      const collar = new THREE.Mesh(
        new THREE.BoxGeometry(w3 * 1.06, 0.36, d3 * 1.06),
        new THREE.MeshStandardMaterial({ map: three.textures.hazardRed, roughness: 0.58 })
      );
      collar.position.y = 0.18;
      addPart(collar);

      const col = new THREE.Mesh(
        new THREE.BoxGeometry(w3 * 0.88, 1.80, d3 * 0.88),
        new THREE.MeshStandardMaterial({ color: 0x64748b, roughness: 0.62, metalness: 0.28 })
      );
      col.position.y = 1.26;
      addPart(col);

      const cap = new THREE.Mesh(
        new THREE.BoxGeometry(w3 * 1.04, 0.14, d3 * 1.04),
        new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.45, metalness: 0.65 })
      );
      cap.position.y = 2.18;
      addPart(cap);
    } else {
      // Banda transportadora motorizada con patas, rieles y rodillos metalicos
      const frameMat = new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.45, metalness: 0.68 });
      [[-w3 * 0.42, -d3 * 0.36], [w3 * 0.42, -d3 * 0.36], [-w3 * 0.42, d3 * 0.36], [w3 * 0.42, d3 * 0.36]].forEach(([lx, lz]) => {
        const leg = new THREE.Mesh(new THREE.BoxGeometry(0.10, 0.46, 0.10), frameMat);
        leg.position.set(lx, 0.23, lz);
        addPart(leg);
      });

      const frame = new THREE.Mesh(new THREE.BoxGeometry(w3, 0.22, d3 * 0.94), frameMat);
      frame.position.y = 0.50;
      addPart(frame);

      const belt = new THREE.Mesh(
        new THREE.BoxGeometry(w3 * 0.96, 0.08, d3 * 0.78),
        new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.92 })
      );
      belt.position.y = 0.64;
      addPart(belt);

      const motor = new THREE.Mesh(
        new THREE.CylinderGeometry(0.14, 0.14, 0.28, 14),
        new THREE.MeshStandardMaterial({ color: 0x0284c7, roughness: 0.4, metalness: 0.5 })
      );
      motor.rotation.x = Math.PI / 2;
      motor.position.set(-w3 * 0.36, 0.46, d3 * 0.55);
      addPart(motor);

      const rollerMat = new THREE.MeshStandardMaterial({ color: 0xcbd5e1, metalness: 0.85, roughness: 0.22 });
      const steps = Math.max(4, Math.floor(w3 * 2.2));
      for (let r = 0; r < steps; r++) {
        const rx = -w3 * 0.43 + (r / (steps - 1)) * (w3 * 0.86);
        const roller = new THREE.Mesh(new THREE.CylinderGeometry(0.068, 0.068, d3 * 0.96, 12), rollerMat);
        roller.rotation.x = Math.PI / 2;
        roller.position.set(rx, 0.64, 0);
        addPart(roller);
      }
    }
    return group;
  }

  function getActiveObstaclesList() {
    const list = [...state.obstacles];
    if (state.unexpectedActive && state.unexpectedSpec) {
      list.push(state.unexpectedSpec);
    }
    return list;
  }

  function refreshInteractiveMeshesCache() {
    const list = [];
    three.obstacleGroups.forEach((g) => {
      g.children.forEach((c) => {
        if (!c.isSprite) list.push(c);
      });
    });
    three.waypointGroups.forEach((g) => {
      g.children.forEach((c) => {
        if (!c.isSprite) list.push(c);
      });
    });
    three.interactiveMeshes = list;
  }

  function rebuildThreeObstaclesAndWaypoints() {
    if (!three.scene || !window.THREE) return;
    const THREE = window.THREE;

    three.obstacleGroups.forEach((g) => {
      three.scene.remove(g);
      disposeObject3D(g);
    });
    three.obstacleGroups = [];
    three.emergencyBeacons = [];

    const allObs = getActiveObstaclesList();
    allObs.forEach((ob, idx) => {
      const grp = createObstacleGroup(ob, idx);
      three.scene.add(grp);
      three.obstacleGroups.push(grp);
    });

    three.waypointGroups.forEach((g) => {
      three.scene.remove(g);
      disposeObject3D(g);
    });
    three.waypointGroups = [];
    if (three.floorPartMesh) {
      three.scene.remove(three.floorPartMesh);
      disposeObject3D(three.floorPartMesh);
      three.floorPartMesh = null;
    }
    if (three.deliveredPartMesh) {
      three.scene.remove(three.deliveredPartMesh);
      disposeObject3D(three.deliveredPartMesh);
      three.deliveredPartMesh = null;
    }

    state.waypoints.forEach((wp, idx) => {
      const grp = new THREE.Group();
      const pos3 = to3D(wp.x, wp.y);
      grp.position.set(pos3.x, 0.02, pos3.z);

      const colorHex = wp.action === "pick" ? 0x38bdf8 : wp.action === "place" ? 0xa855f7 : 0xef4444;

      const pad = new THREE.Mesh(
        new THREE.CylinderGeometry(0.42, 0.46, 0.08, 24),
        new THREE.MeshStandardMaterial({ color: 0x334155, metalness: 0.7, roughness: 0.3 })
      );
      pad.position.y = 0.04;
      pad.userData = { dragType: "waypoint", index: idx, label: wp.label, parentGroup: grp };
      grp.add(pad);

      const ring = new THREE.Mesh(
        new THREE.TorusGeometry(0.44, 0.048, 12, 32),
        new THREE.MeshBasicMaterial({ color: colorHex })
      );
      ring.rotation.x = Math.PI / 2;
      ring.position.y = 0.08;
      ring.userData = { dragType: "waypoint", index: idx, label: wp.label, parentGroup: grp };
      grp.add(ring);

      let beacon = null;
      const posts = [];

      if (wp.action === "place") {
        // Tarima receptora con 4 postes guia iluminables (sin cono central que atraviese la pieza)
        const postMat = new THREE.MeshStandardMaterial({ color: 0xa855f7, emissive: 0xa855f7, emissiveIntensity: 0.25, metalness: 0.6, roughness: 0.3 });
        [[-0.31, -0.31], [0.31, -0.31], [-0.31, 0.31], [0.31, 0.31]].forEach(([px, pz]) => {
          const post = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.22, 0.06), postMat);
          post.position.set(px, 0.15, pz);
          post.userData = { dragType: "waypoint", index: idx, label: wp.label, parentGroup: grp };
          grp.add(post);
          posts.push(post);
        });
      } else if (wp.action === "pick") {
        // Plataforma de recoleccion limpia sin pico central
        const dockDisk = new THREE.Mesh(
          new THREE.CylinderGeometry(0.32, 0.34, 0.03, 24),
          new THREE.MeshStandardMaterial({ color: 0x0ea5e9, emissive: 0x0284c7, emissiveIntensity: 0.35 })
        );
        dockDisk.position.y = 0.095;
        dockDisk.userData = { dragType: "waypoint", index: idx, label: wp.label, parentGroup: grp };
        grp.add(dockDisk);
        posts.push(dockDisk);
      } else {
        beacon = new THREE.Mesh(
          new THREE.CylinderGeometry(0.07, 0.13, 0.24, 16),
          new THREE.MeshStandardMaterial({ color: colorHex, emissive: colorHex, emissiveIntensity: 0.4 })
        );
        beacon.position.y = 0.16;
        beacon.userData = { dragType: "waypoint", index: idx, label: wp.label, parentGroup: grp };
        grp.add(beacon);
      }

      // Etiqueta flotante 3D por encima del brazo para no tapar la pieza ni los eslabones
      const badgeTxt = wp.action === "pick" ? "ORIGEN" : wp.action === "place" ? "DESTINO" : "SOLDAR";
      const badgeColor = wp.action === "pick" ? "rgba(2, 132, 199, 0.90)" : wp.action === "place" ? "rgba(126, 34, 206, 0.90)" : "rgba(220, 38, 38, 0.90)";
      const badgeSprite = createStationBadgeSprite(badgeTxt, badgeColor);
      badgeSprite.position.set(0, 1.56, 0);
      grp.add(badgeSprite);

      grp.userData = { ring, beacon, posts, defaultColor: colorHex };
      three.scene.add(grp);
      three.waypointGroups.push(grp);

      // Pieza 3D esperando en la estacion de origen (pick)
      if (wp.action === "pick") {
        three.floorPartMesh = new THREE.Group();
        populateCargoMeshGroup(three.floorPartMesh, state.cargoId);
        three.floorPartMesh.scale.set(0.84, 0.84, 0.84);
        three.floorPartMesh.position.set(pos3.x, 0.23, pos3.z);
        three.floorPartMesh.visible = !state.carryingPart && !state.deliveredPart;
        three.scene.add(three.floorPartMesh);
      }

      // Pieza 3D entregada en la estacion destino (place)
      if (wp.action === "place") {
        three.deliveredPartMesh = new THREE.Group();
        populateCargoMeshGroup(three.deliveredPartMesh, state.cargoId);
        three.deliveredPartMesh.scale.set(0.84, 0.84, 0.84);
        three.deliveredPartMesh.position.set(pos3.x, 0.23, pos3.z);
        three.deliveredPartMesh.visible = Boolean(state.deliveredPart);
        three.scene.add(three.deliveredPartMesh);
      }
    });

    refreshInteractiveMeshesCache();
  }

  function updateWaypointVisuals(completedCount) {
    three.waypointGroups.forEach((grp, idx) => {
      const done = idx < completedCount;
      const colorHex = done ? 0x22c55e : grp.userData.defaultColor;
      grp.userData.ring.material.color.setHex(colorHex);
      if (grp.userData.beacon) {
        grp.userData.beacon.material.color.setHex(colorHex);
        grp.userData.beacon.material.emissive.setHex(colorHex);
      }
      if (grp.userData.posts && grp.userData.posts.length) {
        grp.userData.posts.forEach((p) => {
          p.material.color.setHex(colorHex);
          if (p.material.emissive) p.material.emissive.setHex(colorHex);
        });
      }
    });
  }

  function updateTelemetryHud(deg1, deg2, isPreview = false) {
    if (!el.telemetryHud) return;
    if (isPreview) {
      el.telemetryHud.textContent = `Vista previa: ${Math.round(deg1)}° / ${Math.round(deg2)}°`;
      return;
    }
    const cargoSpec = getActiveCargoSpec();
    const cargoNote = state.carryingPart
      ? ` · Llevando ${cargoSpec.short_name} (${cargoSpec.weight_kg} kg)`
      : state.deliveredPart
        ? ` · Carga entregada (${cargoSpec.short_name})`
        : " · Pinza libre";
    el.telemetryHud.textContent = `${Math.round(deg1)}° / ${Math.round(deg2)}°${cargoNote}`;
  }

  function syncPlayButton() {
    if (!el.btnPlayPause) return;
    if (state.phase === "done" || state.phase === "failed") {
      el.btnPlayPause.textContent = "Reproducir";
    } else if (state.paused) {
      el.btnPlayPause.textContent = "Reanudar";
    } else {
      el.btnPlayPause.textContent = "Pausar";
    }
  }

  function setRobotAnglesDeg(deg1, deg2) {
    state.liveDeg = [deg1, deg2];
    if (!state.cspaceHover) {
      updateTelemetryHud(deg1, deg2, false);
    }
    if (!three.shoulderGroup || !three.elbowGroup) return;
    three.shoulderGroup.rotation.y = (deg1 * Math.PI) / 180;
    three.elbowGroup.rotation.y = (deg2 * Math.PI) / 180;
  }

  function setGhostAnglesDeg(deg1, deg2, visible, isCollision = false) {
    if (!three.ghostShoulder || !three.ghostElbow || !three.ghostMat) return;
    three.ghostShoulder.visible = visible;
    if (visible) {
      three.ghostMat.color.setHex(isCollision ? 0xef4444 : 0x38bdf8);
      three.ghostMat.opacity = isCollision ? 0.52 : 0.32;
      three.ghostShoulder.rotation.y = (deg1 * Math.PI) / 180;
      three.ghostElbow.rotation.y = (deg2 * Math.PI) / 180;
    }
  }

  function startRenderLoop() {
    function loop(now) {
      if (!shouldRunRenderLoop()) {
        state.rafId = null;
        return;
      }

      updateAnimationTick(now);

      three.camTheta += (three.targetCamTheta - three.camTheta) * 0.14;
      three.camPhi += (three.targetCamPhi - three.camPhi) * 0.14;
      three.camRadius += (three.targetCamRadius - three.camRadius) * 0.14;
      updateCameraPosition();

      three.waypointGroups.forEach((grp, i) => {
        const pulse = 1 + Math.sin(now * 0.005 + i) * 0.08;
        grp.userData.ring.scale.set(pulse, pulse, 1);
      });

      // Animacion fisica de cierre de mordazas y halo magnetico al transportar carga
      const targetJawOffset = state.carryingPart ? 0.16 : 0.28;
      if (three.gripperLeft && three.gripperRight) {
        three.gripperLeft.position.z += (targetJawOffset - three.gripperLeft.position.z) * 0.22;
        three.gripperRight.position.z += (-targetJawOffset - three.gripperRight.position.z) * 0.22;
      }
      if (three.clampHalo) {
        three.clampHalo.visible = state.carryingPart;
        if (state.carryingPart) {
          const haloPulse = 1 + Math.sin(now * 0.01) * 0.12;
          three.clampHalo.scale.set(haloPulse, haloPulse, 1);
        }
      }
      if (three.cargoLaser) {
        three.cargoLaser.visible = state.carryingPart;
      }
      if (three.floorPartMesh && three.floorPartMesh.visible) {
        three.floorPartMesh.position.y = 0.23 + Math.sin(now * 0.004) * 0.018;
      }

      // Baliza pulsante para obstaculo imprevisto y anillo LED de estado del pedestal
      if (three.emergencyBeacons.length) {
        const pulseI = 0.55 + 0.45 * Math.sin(now * 0.012);
        three.emergencyBeacons.forEach((b) => {
          b.material.emissiveIntensity = pulseI;
        });
      }
      if (three.statusRing) {
        const ringColor = state.phase === "failed"
          ? 0xef4444
          : state.carryingPart
            ? 0x38bdf8
            : (state.phase === "exploring" || state.phase === "dwell")
              ? 0xfbbf24
              : state.phase === "done"
                ? 0x22c55e
                : 0x4fd1c5;
        three.statusRing.material.color.setHex(ringColor);
      }

      if (three.sparksActive && three.sparkPoints) {
        const pos = three.sparkPoints.geometry.attributes.position.array;
        let anyAbove = false;
        for (let i = 0; i < three.sparkVel.length; i++) {
          const v = three.sparkVel[i];
          pos[i * 3] += v.vx;
          pos[i * 3 + 1] += v.vy;
          pos[i * 3 + 2] += v.vz;
          v.vy -= 0.0045;
          if (pos[i * 3 + 1] > 0.02) anyAbove = true;
        }
        three.sparkPoints.geometry.attributes.position.needsUpdate = true;
        if (!anyAbove) {
          three.sparksActive = false;
          three.sparkPoints.visible = false;
        }
      }

      if (three.shockwaveRing && three.shockwaveRing.visible) {
        three.shockwaveScale += 0.14;
        three.shockwaveRing.scale.set(three.shockwaveScale, three.shockwaveScale, 1);
        three.shockwaveRing.material.opacity -= 0.035;
        if (three.shockwaveRing.material.opacity <= 0) three.shockwaveRing.visible = false;
      }

      if (three.torchLight && three.torchLight.intensity > 0) {
        three.torchLight.intensity = Math.max(0, three.torchLight.intensity - 0.07);
      }

      if (three.renderer && three.scene && three.camera) {
        three.renderer.render(three.scene, three.camera);
      }
      state.rafId = requestAnimationFrame(loop);
    }
    state.rafId = requestAnimationFrame(loop);
  }

  // =========================================================================
  // EJECUCION MULTI-ETAPA Y RECALCULO EN VIVO ANTE IMPREVISTOS
  // =========================================================================
  async function runPythonSequence(customStartDeg = null, fromWaypointIdx = 0) {
    const mySeq = ++state.reqSeq;
    state.phase = "idle";
    state.dwellLeftMs = 0;
    state.pendingNextStage = null;
    state.fromWaypointOffset = fromWaypointIdx;
    cachedBaseStageKey = "";
    cachedExploredKey = "";
    cachedExploredCount = 0;
    three.sparksActive = false;
    if (three.sparkPoints) three.sparkPoints.visible = false;
    updateTrail3D([]);

    const startDeg = customStartDeg || state.startDeg;
    const remainingWaypoints = state.waypoints.slice(fromWaypointIdx);
    const fullOriginLabel = state.waypoints[0] ? state.waypoints[0].label : null;

    if (fromWaypointIdx === 0) {
      state.completedWaypoints = 0;
      state.carryingPart = false;
      state.deliveredPart = false;
      if (three.carriedPartMesh) three.carriedPartMesh.visible = false;
      if (three.deliveredPartMesh) three.deliveredPartMesh.visible = false;
      if (three.floorPartMesh) {
        const pickWp = state.waypoints.find((w) => w.action === "pick");
        if (pickWp) {
          const p3 = to3D(pickWp.x, pickWp.y);
          three.floorPartMesh.position.set(p3.x, 0.23, p3.z);
          three.floorPartMesh.visible = true;
        }
      }
      updateWaypointVisuals(0);
    }

    syncPlayButton();

    try {
      const taskObj = state.meta.tasks.find((t) => t.id === state.activeTaskId);
      const resp = await fetch("/api/arm/solve-sequence", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          task_id: state.activeTaskId,
          task_name: taskObj ? taskObj.name : "Tarea en planta",
          algorithm: state.algorithm,
          cargo_id: state.cargoId,
          origin_station: fullOriginLabel,
          start_deg: startDeg,
          waypoints: remainingWaypoints,
          obstacles: getActiveObstaclesList(),
          had_unexpected: state.unexpectedActive,
          use_memory: state.useMemory,
          record_run: true
        })
      });
      const json = await resp.json();
      if (mySeq !== state.reqSeq) return;
      if (json.status !== "success") {
        state.phase = "failed";
        syncPlayButton();
        el.verdictText.textContent = json.message || "Error al calcular el ciclo en Python.";
        return;
      }

      state.lastResult = json.data;
      state.historyDirty = true;
      updateSummary(json.data, fromWaypointIdx, false);
      startStagePlayback(0, startDeg);
      if (el.logModal.classList.contains("open")) {
        loadHistoryData();
      } else {
        refreshHistoryBadge();
      }
    } catch (err) {
      if (mySeq === state.reqSeq) {
        state.phase = "failed";
        syncPlayButton();
        el.verdictText.textContent = "Error al calcular el ciclo en Python.";
      }
    }
  }

  function startStagePlayback(stageIndex, initialDeg = null) {
    const data = state.lastResult;
    if (!data || !data.stages || !data.stages[stageIndex]) return;

    state.paused = false;
    state.dwellLeftMs = 0;
    state.pendingNextStage = null;
    state.stageIdx = stageIndex;
    state.expCursor = 0;
    state.pathCursor = 0;
    state.lastTickTime = performance.now();

    const st = data.stages[stageIndex];
    if (initialDeg) {
      setRobotAnglesDeg(initialDeg[0], initialDeg[1]);
    } else if (stageIndex === 0) {
      setRobotAnglesDeg(state.startDeg[0], state.startDeg[1]);
    }

    setGhostAnglesDeg(0, 0, false);
    updateTrail3D(st.found ? st.path_frames : [], Boolean(st.carrying_payload || state.carryingPart));

    if (st.explored.length === 0) {
      state.phase = "failed";
      drawCspace(st, 0, -1, state.liveDeg);
      el.phaseBadge.textContent = `Detenido en ${st.label}`;
      el.phaseFill.style.width = "100%";
      updateSummary(data, state.fromWaypointOffset, true);
      syncPlayButton();
      return;
    }
    state.phase = "exploring";
    updateSummary(data, state.fromWaypointOffset, false);
    syncPlayButton();
  }

  function updateAnimationTick(now) {
    if (state.cspaceHover) return;

    const data = state.lastResult;
    if (!data || state.paused || state.phase === "idle" || state.phase === "done" || state.phase === "failed") {
      return;
    }

    const st = data.stages[state.stageIdx];
    if (!st) return;

    const dt = Math.min(0.05, Math.max(0, (now - state.lastTickTime) / 1000));
    state.lastTickTime = now;
    const totalStages = data.stages.length;
    const stageBasePct = (state.stageIdx / totalStages) * 100;
    const stageSpanPct = 100 / totalStages;
    const cargoSpec = getActiveCargoSpec();

    if (state.phase === "dwell") {
      state.dwellLeftMs -= dt * 1000;
      if (state.dwellLeftMs <= 0) {
        const nextInfo = state.pendingNextStage;
        state.pendingNextStage = null;
        if (nextInfo) {
          startStagePlayback(nextInfo[0], [nextInfo[1], nextInfo[2]]);
        }
      }
      return;
    }

    if (state.phase === "exploring") {
      const totalExp = st.explored.length;
      const rate = Math.max(24, totalExp / 2.2) * state.speed;
      state.expCursor = Math.min(totalExp, state.expCursor + rate * dt);

      const idx = Math.max(0, Math.min(totalExp - 1, Math.floor(state.expCursor) - 1));
      const sample = st.explored[idx];
      let liveAngles = state.liveDeg;
      if (sample) {
        const stepDeg = state.meta.step_deg;
        liveAngles = [sample[0] * stepDeg, sample[1] * stepDeg];
        setGhostAnglesDeg(liveAngles[0], liveAngles[1], true, false);
      }

      drawCspace(st, Math.floor(state.expCursor), -1, liveAngles);
      const pct = stageBasePct + (state.expCursor / totalExp) * stageSpanPct * 0.55;
      el.phaseFill.style.width = `${Math.round(pct)}%`;
      el.phaseBadge.textContent = `Etapa ${state.stageIdx + 1}/${totalStages} · Probando ${Math.floor(state.expCursor)}/${totalExp}`;

      if (state.expCursor >= totalExp) {
        setGhostAnglesDeg(0, 0, false);
        if (st.found && st.path_frames.length > 0) {
          state.phase = "moving";
          state.pathCursor = 0;
          updateSummary(data, state.fromWaypointOffset, false);
        } else {
          state.phase = "failed";
          el.phaseBadge.textContent = `Detenido en ${st.label}`;
          updateSummary(data, state.fromWaypointOffset, true);
          syncPlayButton();
        }
      }
    } else if (state.phase === "moving") {
      const frames = st.path_frames;
      state.pathCursor = Math.min(frames.length - 1, state.pathCursor + 18 * state.speed * dt);

      const i0 = Math.floor(state.pathCursor);
      const i1 = Math.min(frames.length - 1, i0 + 1);
      const frac = state.pathCursor - i0;
      const f0 = frames[i0];
      const f1 = frames[i1];

      const interpDeg = (a, b) => {
        const diff = ((b - a + 540) % 360) - 180;
        return (a + diff * frac + 360) % 360;
      };
      const curD1 = interpDeg(f0.deg1, f1.deg1);
      const curD2 = interpDeg(f0.deg2, f1.deg2);
      setRobotAnglesDeg(curD1, curD2);
      drawCspace(st, st.explored.length, i0, [curD1, curD2]);

      const pct = stageBasePct + stageSpanPct * (0.55 + (state.pathCursor / Math.max(1, frames.length - 1)) * 0.45);
      el.phaseFill.style.width = `${Math.round(pct)}%`;
      const loadTag = state.carryingPart ? " · Con carga" : "";
      el.phaseBadge.textContent = `Etapa ${state.stageIdx + 1}/${totalStages}${loadTag} · ${st.label}`;

      if (state.pathCursor >= frames.length - 1) {
        // Accion coordinada al llegar al waypoint
        state.completedWaypoints += 1;
        updateWaypointVisuals(state.completedWaypoints);
        const t3 = to3D(st.target[0], st.target[1]);

        if (st.action === "pick") {
          state.carryingPart = true;
          state.deliveredPart = false;
          if (three.floorPartMesh) three.floorPartMesh.visible = false;
          if (three.carriedPartMesh) three.carriedPartMesh.visible = true;
          setRobotAnglesDeg(curD1, curD2);
          triggerSparks(t3.x, t3.z, 0x38bdf8);

          if (state.stageIdx + 1 < totalStages) {
            state.phase = "dwell";
            state.dwellLeftMs = 280 / Math.max(0.6, state.speed);
            state.pendingNextStage = [state.stageIdx + 1, curD1, curD2];
            el.phaseBadge.textContent = `Pinza cerrada: ${cargoSpec.short_name} (${cargoSpec.weight_kg} kg)`;
            el.verdictText.textContent = `Pieza sujetada en origen (${cargoSpec.short_name}, ${cargoSpec.weight_kg} kg). Trasladando hacia destino...`;
            return;
          }
        } else if (st.action === "place") {
          state.carryingPart = false;
          state.deliveredPart = true;
          if (three.carriedPartMesh) three.carriedPartMesh.visible = false;
          if (three.deliveredPartMesh) {
            three.deliveredPartMesh.position.set(t3.x, 0.23, t3.z);
            three.deliveredPartMesh.visible = true;
          } else if (three.floorPartMesh) {
            three.floorPartMesh.position.set(t3.x, 0.23, t3.z);
            three.floorPartMesh.visible = true;
          }
          setRobotAnglesDeg(curD1, curD2);
          triggerSparks(t3.x, t3.z, 0x22c55e);
        } else {
          triggerSparks(t3.x, t3.z, 0xfbbf24);
        }

        if (state.stageIdx + 1 < totalStages) {
          startStagePlayback(state.stageIdx + 1, [curD1, curD2]);
        } else {
          state.phase = "done";
          el.phaseFill.style.width = "100%";
          el.phaseBadge.textContent = `Entrega completada: ${cargoSpec.short_name} (${cargoSpec.weight_kg} kg)`;
          updateSummary(data, state.fromWaypointOffset, true);
          syncPlayButton();
        }
      }
    }
  }

  /**
   * Clasifica el resultado de una corrida evitando penalizar a A* como
   * "fuera de expectativas" en geometrias complejas donde ya es el minimo optimo.
   */
  function classifyRunOutcome(row) {
    const algoId = row.algorithm_id || (row.algorithm && row.algorithm.id) || "";
    const budgetLimit = row.budget_limit || 900;
    const withinBudget = row.within_budget !== false;

    if (!row.found) {
      return { kind: "fail", tone: "is-fail", badgeTone: "fail", budgetLimit, overBudget: false };
    }
    if (row.is_optimal && (withinBudget || algoId === "astar")) {
      return { kind: "optimal", tone: "is-ok", badgeTone: "ok", budgetLimit, overBudget: !withinBudget };
    }
    if (!withinBudget) {
      return { kind: "over_budget", tone: "is-warn", badgeTone: "warn", budgetLimit, overBudget: true };
    }
    return { kind: "detour", tone: "is-warn", badgeTone: "warn", budgetLimit, overBudget: false };
  }

  function updateSummary(data, offsetWaypoints = 0, isFinal = true) {
    if (!data) return;
    const doneTotal = offsetWaypoints + data.completed_stages;
    const fullTotal = offsetWaypoints + data.total_stages;
    const cargo = data.cargo || getActiveCargoSpec();
    const tax = Number(data.payload_energy_tax || (cargo && cargo.payload_energy_tax) || 0);
    const distM = Number((cargo && cargo.transport_distance_m) || 0);
    const shortCargo = cargo.short_name || cargo.cargo_name || "Carga";
    const weightKg = cargo.weight_kg || 18;

    el.statExpanded.textContent = data.nodes_expanded.toLocaleString("es-MX");
    el.statEnergy.textContent = data.energy > 0
      ? (tax > 0 ? `${data.energy} (+${tax})` : `${data.energy}`)
      : "—";

    el.kpiStatusBox.classList.remove("is-ok", "is-warn", "is-fail");
    el.verdictBox.classList.remove("is-warn", "is-fail");

    if (!isFinal) {
      el.statStatus.textContent = `En curso (${state.stageIdx + 1}/${data.stages.length})`;
      if (state.phase === "moving") {
        el.verdictText.textContent = state.carryingPart
          ? `Llevando ${shortCargo} (${weightKg} kg) hacia la estacion de destino...`
          : `Moviendo pinza hacia la estacion de origen para tomar ${shortCargo} (${weightKg} kg)...`;
      } else {
        el.verdictText.textContent = `Evaluando posturas sin colision con ${data.algorithm.name} para ${shortCargo} (${weightKg} kg)...`;
      }
      return;
    }

    const outcome = classifyRunOutcome(data);
    const memNote = data.from_cache ? " · Desde Memoria SQL" : "";

    if (outcome.kind === "fail") {
      el.statStatus.textContent = `Fallo (${doneTotal}/${fullTotal})`;
      el.kpiStatusBox.classList.add("is-fail");
      el.verdictBox.classList.add("is-fail");
      const abortText = cargo && cargo.picked_up
        ? `${shortCargo} (${weightKg} kg) quedo detenida en ruta.`
        : `No logro recoger ${shortCargo} (${weightKg} kg).`;
      el.verdictText.textContent = `${data.reason || "Camino bloqueado."} ${abortText}`;
    } else if (outcome.kind === "optimal") {
      el.statStatus.textContent = `${fullTotal}/${fullTotal} · ${data.cycle_seconds} s`;
      el.kpiStatusBox.classList.add("is-ok");
      el.verdictText.textContent =
        `Ruta optima en ${data.cycle_seconds} s: entrego ${shortCargo} (${weightKg} kg) en ${distM} m (+${tax} energia por peso).${memNote}`;
    } else if (outcome.kind === "over_budget") {
      el.statStatus.textContent = `Fuera exp. (> ${outcome.budgetLimit})`;
      el.kpiStatusBox.classList.add("is-warn");
      el.verdictBox.classList.add("is-warn");
      el.verdictText.textContent =
        `Entrego ${shortCargo} (${weightKg} kg), pero supero el margen de ${outcome.budgetLimit} posturas (${data.nodes_expanded}).${memNote}`;
    } else {
      el.statStatus.textContent = `${fullTotal}/${fullTotal} · ${data.cycle_seconds} s`;
      el.kpiStatusBox.classList.add("is-warn");
      el.verdictBox.classList.add("is-warn");
      el.verdictText.textContent =
        `Entrego ${shortCargo} (${weightKg} kg), pero dio rodeos que elevaron la energia a ${data.energy} (+${tax} por peso).${memNote}`;
    }
  }

  // =========================================================================
  // MAPA DE POSTURAS + HOVER INTERACTIVO A 3D (CON CACHE OFFSCREEN 60FPS)
  // =========================================================================
  const CSPACE_PAD = { l: 28, b: 24, t: 10, r: 10 };

  function ensureCspaceBaseLayer(stageData) {
    const dark = isDarkTheme();
    const key = `${state.activeTaskId}|${state.algorithm}|${stageData.stage_index}|${dark ? 1 : 0}|${stageData.target.join(",")}|${stageData.nodes_expanded}`;
    if (cachedBaseStageKey === key) return;
    cachedBaseStageKey = key;

    const N = state.meta.grid_n;
    const plotW = cspaceBaseCanvas.width - CSPACE_PAD.l - CSPACE_PAD.r;
    const plotH = cspaceBaseCanvas.height - CSPACE_PAD.t - CSPACE_PAD.b;
    const cw = plotW / N;
    const ch = plotH / N;
    const cspace = stageData.cspace;
    const toPxX = (i1) => CSPACE_PAD.l + i1 * cw;
    const toPxY = (i2) => CSPACE_PAD.t + (N - 1 - i2) * ch;

    cspaceBaseCtx.fillStyle = dark ? "#161F28" : "#F7F8F4";
    cspaceBaseCtx.fillRect(0, 0, cspaceBaseCanvas.width, cspaceBaseCanvas.height);

    cspaceBaseCtx.fillStyle = dark ? "#1C2733" : "#FFFFFF";
    cspaceBaseCtx.fillRect(CSPACE_PAD.l, CSPACE_PAD.t, plotW, plotH);

    for (let i1 = 0; i1 < N; i1++) {
      const row = cspace[i1];
      for (let i2 = 0; i2 < N; i2++) {
        const val = row[i2];
        if (val === 1) {
          cspaceBaseCtx.fillStyle = dark ? "#7C2D2D" : "#B94A4A";
          cspaceBaseCtx.fillRect(toPxX(i1), toPxY(i2), cw + 0.4, ch + 0.4);
        } else if (val === 2) {
          cspaceBaseCtx.fillStyle = "#22C55E";
          cspaceBaseCtx.fillRect(toPxX(i1), toPxY(i2), cw + 0.5, ch + 0.5);
        }
      }
    }

    cspaceBaseCtx.strokeStyle = dark ? "rgba(232,228,216,0.22)" : "rgba(30,42,51,0.22)";
    cspaceBaseCtx.lineWidth = 1;
    cspaceBaseCtx.strokeRect(CSPACE_PAD.l, CSPACE_PAD.t, plotW, plotH);

    cspaceBaseCtx.fillStyle = dark ? "#A9B0AC" : "#4B5A61";
    cspaceBaseCtx.font = "600 10px 'IBM Plex Sans', sans-serif";
    cspaceBaseCtx.textAlign = "center";
    cspaceBaseCtx.fillText("Giro del hombro (0° a 360°)", CSPACE_PAD.l + plotW / 2, cspaceBaseCanvas.height - 6);

    cspaceBaseCtx.save();
    cspaceBaseCtx.translate(11, CSPACE_PAD.t + plotH / 2);
    cspaceBaseCtx.rotate(-Math.PI / 2);
    cspaceBaseCtx.fillText("Giro del codo (0° a 360°)", 0, 0);
    cspaceBaseCtx.restore();
  }

  function syncExploredCache(stageData, expCount) {
    const dark = isDarkTheme();
    const N = state.meta.grid_n;
    const plotW = el.csCanvas.width - CSPACE_PAD.l - CSPACE_PAD.r;
    const plotH = el.csCanvas.height - CSPACE_PAD.t - CSPACE_PAD.b;
    const cw = plotW / N;
    const ch = plotH / N;
    const cspace = stageData.cspace;
    const toPxX = (i1) => CSPACE_PAD.l + i1 * cw;
    const toPxY = (i2) => CSPACE_PAD.t + (N - 1 - i2) * ch;

    const totalExp = Math.max(1, stageData.explored.length);
    const clampedCount = Math.max(0, Math.min(expCount, stageData.explored.length));
    const key = cachedBaseStageKey;

    if (cachedExploredKey !== key || clampedCount < cachedExploredCount) {
      cspaceExploredCtx.drawImage(cspaceBaseCanvas, 0, 0);
      cachedExploredKey = key;
      cachedExploredCount = 0;
    }

    for (let k = cachedExploredCount; k < clampedCount; k++) {
      const [e1, e2] = stageData.explored[k];
      if (cspace[e1][e2] === 2) continue;
      const ratio = k / totalExp;
      if (ratio < 0.45) cspaceExploredCtx.fillStyle = dark ? "rgba(56,142,130,0.52)" : "rgba(47,111,99,0.45)";
      else if (ratio < 0.85) cspaceExploredCtx.fillStyle = dark ? "rgba(79,184,168,0.68)" : "rgba(59,154,140,0.65)";
      else cspaceExploredCtx.fillStyle = dark ? "rgba(125,226,209,0.85)" : "rgba(38,166,154,0.82)";
      cspaceExploredCtx.fillRect(toPxX(e1), toPxY(e2), cw + 0.3, ch + 0.3);
    }
    cachedExploredCount = clampedCount;
  }

  function drawCspace(stageData, expCount, activePathIdx, liveDeg = null) {
    if (!stageData) return;
    ensureCspaceBaseLayer(stageData);
    syncExploredCache(stageData, expCount);
    csCtx.drawImage(cspaceExploredCanvas, 0, 0);

    const N = state.meta.grid_n;
    const plotW = el.csCanvas.width - CSPACE_PAD.l - CSPACE_PAD.r;
    const plotH = el.csCanvas.height - CSPACE_PAD.t - CSPACE_PAD.b;
    const cw = plotW / N;
    const ch = plotH / N;
    const toPxX = (i1) => CSPACE_PAD.l + i1 * cw;
    const toPxY = (i2) => CSPACE_PAD.t + (N - 1 - i2) * ch;

    if (activePathIdx >= 0 && stageData.path.length > 1) {
      const limit = Math.min(activePathIdx + 1, stageData.path.length);
      csCtx.save();
      csCtx.lineCap = "round";
      csCtx.lineJoin = "round";
      csCtx.strokeStyle = "#F59E0B";
      csCtx.lineWidth = 3.2;
      csCtx.beginPath();
      for (let p = 0; p < limit; p++) {
        const [p1, p2] = stageData.path[p];
        const px = toPxX(p1) + cw / 2;
        const py = toPxY(p2) + ch / 2;
        if (p === 0) csCtx.moveTo(px, py);
        else {
          const [prev1, prev2] = stageData.path[p - 1];
          if (Math.abs(p1 - prev1) > 4 || Math.abs(p2 - prev2) > 4) csCtx.moveTo(px, py);
          else csCtx.lineTo(px, py);
        }
      }
      csCtx.stroke();
      csCtx.restore();
    }

    const [s1, s2] = stageData.start;
    csCtx.fillStyle = "#3B82F6";
    csCtx.strokeStyle = "#FFFFFF";
    csCtx.lineWidth = 1.6;
    csCtx.beginPath();
    csCtx.arc(toPxX(s1) + cw / 2, toPxY(s2) + ch / 2, 4.5, 0, Math.PI * 2);
    csCtx.fill();
    csCtx.stroke();

    if (liveDeg) {
      const stepDeg = state.meta.step_deg;
      const li1 = (liveDeg[0] / stepDeg) % N;
      const li2 = (liveDeg[1] / stepDeg) % N;
      csCtx.strokeStyle = "#FFFFFF";
      csCtx.lineWidth = 1.6;
      csCtx.beginPath();
      csCtx.arc(toPxX(li1) + cw / 2, toPxY(li2) + ch / 2, 5.5, 0, Math.PI * 2);
      csCtx.stroke();
    }
  }

  function redrawCurrentCspace() {
    if (!state.lastResult || !state.lastResult.stages[state.stageIdx]) return;
    const st = state.lastResult.stages[state.stageIdx];
    const expCount = state.phase === "moving" || state.phase === "dwell" || state.phase === "done"
      ? st.explored.length
      : Math.floor(state.expCursor);
    const activePathIdx = state.phase === "moving"
      ? Math.floor(state.pathCursor)
      : (state.phase === "dwell" || state.phase === "done")
        ? st.path.length - 1
        : -1;
    drawCspace(st, expCount, activePathIdx, state.liveDeg);
  }

  function selectAlgorithm(algoId, solveNow = true) {
    if (!algoId) return;
    state.algorithm = algoId;
    el.algoPills.forEach((p) => {
      const active = p.dataset.algo === algoId;
      p.classList.toggle("active", active);
      p.setAttribute("aria-selected", active ? "true" : "false");
    });
    if (solveNow) runPythonSequence();
  }

  // =========================================================================
  // EVENTOS UI (INDEPENDIENTES DE THREE.JS, ENLAZADOS UNA SOLA VEZ)
  // =========================================================================
  function bindUiEvents() {
    if (state.uiBound) return;
    state.uiBound = true;

    el.algoPills.forEach((pill) => {
      pill.addEventListener("click", () => {
        selectAlgorithm(pill.dataset.algo, true);
      });
    });

    el.btnEmergency.addEventListener("click", () => {
      state.unexpectedActive = !state.unexpectedActive;
      el.btnEmergency.classList.toggle("active", state.unexpectedActive);
      el.btnEmergency.textContent = state.unexpectedActive ? "Quitar imprevisto" : "Imprevisto";
      rebuildThreeObstaclesAndWaypoints();

      // Si el robot iba a medio ciclo, recalcular desde su postura y etapa actual (Opcion C real)
      const inMidCycle = state.unexpectedActive &&
        (state.phase === "exploring" || state.phase === "moving" || state.phase === "dwell") &&
        state.completedWaypoints < state.waypoints.length;

      if (inMidCycle) {
        const useLiveAngles = state.phase === "moving" || state.phase === "dwell" || state.completedWaypoints > 0;
        runPythonSequence(useLiveAngles ? [...state.liveDeg] : null, state.completedWaypoints);
      } else {
        runPythonSequence();
      }
    });

    el.btnPlayPause.addEventListener("click", () => {
      if (state.phase === "done" || state.phase === "failed") {
        runPythonSequence();
        return;
      }
      state.paused = !state.paused;
      syncPlayButton();
      if (!state.paused) {
        state.lastTickTime = performance.now();
        ensureRenderLoop();
      }
    });

    el.btnReplay.addEventListener("click", () => {
      runPythonSequence();
    });

    el.btnReset.addEventListener("click", () => {
      loadTask(state.activeTaskId, true);
    });

    if (el.cargoSelect) {
      el.cargoSelect.addEventListener("change", () => {
        state.cargoId = el.cargoSelect.value || "battery_module";
        if (three.ready) {
          refreshCarriedCargoMesh();
          rebuildThreeObstaclesAndWaypoints();
        }
        runPythonSequence();
      });
    }

    el.speedBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        state.speed = parseFloat(btn.dataset.speed) || 1.0;
        el.speedBtns.forEach((b) => b.classList.toggle("active", b === btn));
      });
    });

    el.camBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        el.camBtns.forEach((b) => b.classList.toggle("active", b === btn));
        if (btn.dataset.cam === "top") {
          three.targetCamTheta = 0.0;
          three.targetCamPhi = 0.08;
          three.targetCamRadius = 14.5;
        } else {
          three.targetCamTheta = 0.48;
          three.targetCamPhi = 0.80;
          three.targetCamRadius = 13.6;
        }
      });
    });

    // Modales del Brazo Robotico (cierre seguro sin cerrar al arrastrar seleccion)
    el.btnCompare.addEventListener("click", openCompareModal);
    el.compareClose.addEventListener("click", () => closeCompareModal(true));
    if (window.bindSafeBackdropClose) {
      window.bindSafeBackdropClose(el.compareModal, () => closeCompareModal(true));
    } else {
      el.compareModal.addEventListener("click", (e) => {
        if (e.target === el.compareModal) closeCompareModal(true);
      });
    }

    el.btnHistory.addEventListener("click", openLogModal);
    el.logClose.addEventListener("click", () => closeLogModal(true));
    if (window.bindSafeBackdropClose) {
      window.bindSafeBackdropClose(el.logModal, () => closeLogModal(true));
    } else {
      el.logModal.addEventListener("click", (e) => {
        if (e.target === el.logModal) closeLogModal(true);
      });
    }

    // Navegacion fluida directa entre Comparativa y Bitacora SQL
    if (el.switchToLog) {
      el.switchToLog.addEventListener("click", () => {
        openLogModal();
      });
    }
    if (el.switchToCompare) {
      el.switchToCompare.addEventListener("click", () => {
        openCompareModal();
      });
    }

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        let closed = false;
        if (el.compareModal.classList.contains("open")) {
          closeCompareModal(true);
          closed = true;
        }
        if (el.logModal.classList.contains("open")) {
          closeLogModal(true);
          closed = true;
        }
        if (closed) e.preventDefault();
        return;
      }

      if (e.code === "Space") {
        const tag = (e.target && e.target.tagName) ? e.target.tagName.toUpperCase() : "";
        const isTyping = tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || tag === "BUTTON" || tag === "A";
        if (!isTyping && !isAnyModalOpen() && isBrazoSectionActive()) {
          e.preventDefault();
          el.btnPlayPause.click();
        }
      }
    });

    // Pestanas accesibles con clic y flechas de teclado en Bitacora SQL
    const tabList = Array.from(el.logTabs);
    tabList.forEach((tab, idx) => {
      tab.addEventListener("click", () => switchLogTab(tab.dataset.armTab));
      tab.addEventListener("keydown", (e) => {
        let nextIdx = -1;
        if (e.key === "ArrowRight") nextIdx = (idx + 1) % tabList.length;
        else if (e.key === "ArrowLeft") nextIdx = (idx - 1 + tabList.length) % tabList.length;
        else if (e.key === "Home") nextIdx = 0;
        else if (e.key === "End") nextIdx = tabList.length - 1;
        if (nextIdx >= 0) {
          e.preventDefault();
          tabList[nextIdx].focus();
          switchLogTab(tabList[nextIdx].dataset.armTab);
        }
      });
    });

    el.ragChips.forEach((chip) => {
      chip.addEventListener("click", () => {
        el.ragChips.forEach((c) => c.classList.toggle("active", c === chip));
        el.ragInput.value = chip.dataset.ragQ;
        runRagQuery(chip.dataset.ragQ);
      });
    });
    el.ragInput.addEventListener("input", () => {
      el.ragChips.forEach((c) => c.classList.remove("active"));
    });
    el.ragForm.addEventListener("submit", (e) => {
      e.preventDefault();
      runRagQuery(el.ragInput.value);
    });

    el.sqlFilters.forEach((btn) => {
      btn.addEventListener("click", () => {
        const nextFilter = btn.dataset.sqlFilter;
        if (state.sqlFilter === nextFilter && !state.historyDirty) return;
        state.sqlFilter = nextFilter;
        el.sqlFilters.forEach((b) => b.classList.toggle("active", b === btn));
        loadHistoryData(true);
      });
    });

    el.btnClearRuns.addEventListener("click", () => handleConfirmClear(el.btnClearRuns, "runs", "Limpiar historial"));
    el.btnClearCache.addEventListener("click", () => handleConfirmClear(el.btnClearCache, "cache", "Vaciar memoria"));
    el.toggleMemory.addEventListener("change", () => {
      state.useMemory = el.toggleMemory.checked;
    });

    // Pausar render WebGL cuando la pestana del navegador no es visible o hay un modal abierto
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) {
        stopRenderLoop();
      } else {
        ensureRenderLoop();
      }
    });
    window.addEventListener("modalLockChange", (e) => {
      if (e.detail && e.detail.open) {
        stopRenderLoop();
      } else {
        ensureRenderLoop();
      }
    });

    // Hover o toque en el mapa C-Space -> mueve el brazo fantasma 3D al instante
    const previewCspacePointer = (e) => {
      if (!state.lastResult || !state.lastResult.stages[state.stageIdx]) return;
      const st = state.lastResult.stages[state.stageIdx];
      const rect = el.csCanvas.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * el.csCanvas.width;
      const y = ((e.clientY - rect.top) / rect.height) * el.csCanvas.height;
      const plotW = el.csCanvas.width - CSPACE_PAD.l - CSPACE_PAD.r;
      const plotH = el.csCanvas.height - CSPACE_PAD.t - CSPACE_PAD.b;
      const N = state.meta.grid_n;

      const i1 = Math.floor(((x - CSPACE_PAD.l) / plotW) * N);
      const i2 = N - 1 - Math.floor(((y - CSPACE_PAD.t) / plotH) * N);
      if (i1 < 0 || i1 >= N || i2 < 0 || i2 >= N) {
        state.cspaceHover = null;
        setGhostAnglesDeg(0, 0, false);
        el.hoverHud.hidden = true;
        return;
      }

      const val = st.cspace[i1][i2];
      const d1 = i1 * state.meta.step_deg;
      const d2 = i2 * state.meta.step_deg;
      state.cspaceHover = { i1, i2, val };
      setGhostAnglesDeg(d1, d2, true, val === 1);
      updateTelemetryHud(d1, d2, true);
      el.hoverHud.textContent = val === 1
        ? `Postura (${d1}°, ${d2}°) — ¡Choca con una maquina!`
        : val === 2
          ? `Postura (${d1}°, ${d2}°) — Alcanza el punto objetivo`
          : `Postura (${d1}°, ${d2}°) — Movimiento libre`;
      el.hoverHud.hidden = false;
    };

    const clearCspacePreview = () => {
      state.cspaceHover = null;
      setGhostAnglesDeg(0, 0, false);
      updateTelemetryHud(state.liveDeg[0], state.liveDeg[1], false);
      el.hoverHud.hidden = true;
      state.lastTickTime = performance.now();
    };

    el.csCanvas.addEventListener("pointerdown", previewCspacePointer);
    el.csCanvas.addEventListener("pointermove", previewCspacePointer);
    el.csCanvas.addEventListener("pointerup", (e) => {
      if (e.pointerType !== "mouse") clearCspacePreview();
    });
    el.csCanvas.addEventListener("pointercancel", clearCspacePreview);
    el.csCanvas.addEventListener("pointerleave", clearCspacePreview);

    const themeBtn = document.getElementById("btnThemeToggle");
    if (themeBtn) {
      themeBtn.addEventListener("click", () => {
        setTimeout(() => {
          updateSceneTheme();
          cachedBaseStageKey = "";
          cachedExploredKey = "";
          cachedExploredCount = 0;
          redrawCurrentCspace();
          if (three.ready && three.renderer && three.scene && three.camera) {
            three.renderer.render(three.scene, three.camera);
          }
        }, 40);
      });
    }
  }

  // =========================================================================
  // EVENTOS DE INTERACCION 3D (RAYCASTING SIN ALLOCACIONES POR FRAME)
  // =========================================================================
  function bindThreePointerEvents() {
    if (state.threePointerBound) return;
    const domEl = three.renderer ? three.renderer.domElement : null;
    if (!domEl) return;
    state.threePointerBound = true;

    const updateNdc = (evt) => {
      const rect = domEl.getBoundingClientRect();
      three.pointerNdc.set(
        ((evt.clientX - rect.left) / rect.width) * 2 - 1,
        -((evt.clientY - rect.top) / rect.height) * 2 + 1
      );
      return three.pointerNdc;
    };

    domEl.addEventListener("pointerdown", (e) => {
      three.raycaster.setFromCamera(updateNdc(e), three.camera);
      const hits = three.raycaster.intersectObjects(three.interactiveMeshes, false);
      three.raycaster.ray.intersectPlane(three.floorPlane, three.floorHitVec);

      if (hits.length > 0) {
        const meta = hits[0].object.userData;
        const grp = meta.parentGroup;
        three.dragTarget = {
          type: meta.dragType,
          index: meta.index,
          offsetX: grp.position.x - three.floorHitVec.x,
          offsetZ: grp.position.z - three.floorHitVec.z
        };
        domEl.style.cursor = "grabbing";
      } else {
        three.dragTarget = { type: "orbit", lastX: e.clientX, lastY: e.clientY };
        domEl.style.cursor = "move";
      }
      domEl.setPointerCapture(e.pointerId);
    });

    domEl.addEventListener("pointermove", (e) => {
      if (isAnyModalOpen()) return;

      if (!three.dragTarget) {
        if (e.pointerType !== "mouse") return;
        three.raycaster.setFromCamera(updateNdc(e), three.camera);
        const hits = three.raycaster.intersectObjects(three.interactiveMeshes, false);
        if (hits.length > 0) {
          const label = hits[0].object.userData.label || "Elemento";
          el.hoverHud.textContent = `${label} — Arrastra para mover`;
          el.hoverHud.hidden = false;
          domEl.style.cursor = "grab";
        } else if (!state.cspaceHover) {
          el.hoverHud.hidden = true;
          domEl.style.cursor = "default";
        }
        return;
      }

      if (three.dragTarget.type === "orbit") {
        const dx = e.clientX - three.dragTarget.lastX;
        const dy = e.clientY - three.dragTarget.lastY;
        three.dragTarget.lastX = e.clientX;
        three.dragTarget.lastY = e.clientY;
        three.targetCamTheta -= dx * 0.009;
        three.targetCamPhi = Math.max(0.08, Math.min(1.25, three.targetCamPhi - dy * 0.009));
        return;
      }

      three.raycaster.setFromCamera(updateNdc(e), three.camera);
      if (!three.raycaster.ray.intersectPlane(three.floorPlane, three.floorHitVec)) return;

      const nx = three.floorHitVec.x + three.dragTarget.offsetX;
      const nz = three.floorHitVec.z + three.dragTarget.offsetZ;
      const p2d = to2D(nx, nz);

      if (three.dragTarget.type === "waypoint") {
        const wp = state.waypoints[three.dragTarget.index];
        wp.x = Math.max(25, Math.min(415, p2d.x));
        wp.y = Math.max(25, Math.min(355, p2d.y));
        const clamped3 = to3D(wp.x, wp.y);
        three.waypointGroups[three.dragTarget.index].position.set(clamped3.x, 0.02, clamped3.z);
        if (wp.action === "pick" && three.floorPartMesh && !state.carryingPart) {
          three.floorPartMesh.position.set(clamped3.x, 0.23, clamped3.z);
        } else if (wp.action === "place" && three.deliveredPartMesh) {
          three.deliveredPartMesh.position.set(clamped3.x, 0.23, clamped3.z);
        }
      } else if (three.dragTarget.type === "obstacle") {
        const idx = three.dragTarget.index;
        const ob = idx < state.obstacles.length ? state.obstacles[idx] : state.unexpectedSpec;
        if (ob) {
          let nextX = Math.max(10, Math.min(430 - ob.w, p2d.x - ob.w / 2));
          let nextY = Math.max(10, Math.min(370 - ob.h, p2d.y - ob.h / 2));

          // Evitar superponer obstaculos directamente sobre el pedestal central del brazo (220, 215)
          const cx = nextX + ob.w / 2;
          const cy = nextY + ob.h / 2;
          const minDx = ob.w / 2 + 24;
          const minDy = ob.h / 2 + 24;
          const relX = cx - BASE_2D[0];
          const relY = cy - BASE_2D[1];
          if (Math.abs(relX) < minDx && Math.abs(relY) < minDy) {
            const pushX = minDx - Math.abs(relX);
            const pushY = minDy - Math.abs(relY);
            if (pushX < pushY) {
              nextX += (relX >= 0 ? pushX : -pushX);
            } else {
              nextY += (relY >= 0 ? pushY : -pushY);
            }
            nextX = Math.max(10, Math.min(430 - ob.w, nextX));
            nextY = Math.max(10, Math.min(370 - ob.h, nextY));
          }

          ob.x = nextX;
          ob.y = nextY;
          const clamped3 = to3D(ob.x + ob.w / 2, ob.y + ob.h / 2);
          const grp = three.obstacleGroups[idx];
          grp.position.x = clamped3.x;
          grp.position.z = clamped3.z;
        }
      }
    });

    const endDrag = () => {
      if (!three.dragTarget) return;
      const wasOrbit = three.dragTarget.type === "orbit";
      three.dragTarget = null;
      domEl.style.cursor = "default";
      if (!wasOrbit) runPythonSequence();
    };
    domEl.addEventListener("pointerup", endDrag);
    domEl.addEventListener("pointercancel", endDrag);

    domEl.addEventListener("wheel", (e) => {
      e.preventDefault();
      three.targetCamRadius = Math.max(7.5, Math.min(19.0, three.targetCamRadius + e.deltaY * 0.008));
    }, { passive: false });
  }

  // =========================================================================
  // GESTION FLUIDA DE MODALES (FOCO, SCROLL, CAMBIO DIRECTO Y CIERRE SEGURO)
  // =========================================================================
  function syncModalLock() {
    if (window.syncGlobalModalLock) {
      window.syncGlobalModalLock();
      return;
    }
    const anyOpen = el.compareModal.classList.contains("open") || el.logModal.classList.contains("open");
    document.documentElement.classList.toggle("arm-modal-lock", anyOpen);
    document.body.classList.toggle("arm-modal-lock", anyOpen);
    if (anyOpen) stopRenderLoop();
    else ensureRenderLoop();
  }

  function resetConfirmButtons() {
    [
      [el.btnClearRuns, "runs", "Limpiar historial"],
      [el.btnClearCache, "cache", "Vaciar memoria"]
    ].forEach(([btn, key, label]) => {
      if (!btn) return;
      if (state.confirmTimers[key]) {
        clearTimeout(state.confirmTimers[key]);
        delete state.confirmTimers[key];
      }
      delete btn.dataset.confirmPending;
      btn.classList.remove("arm-btn-confirm");
      btn.textContent = label;
    });
  }

  function handleConfirmClear(btn, scope, defaultLabel) {
    if (!btn) return;
    if (btn.dataset.confirmPending === "1") {
      resetConfirmButtons();
      clearStorage(scope);
      return;
    }
    btn.dataset.confirmPending = "1";
    btn.classList.add("arm-btn-confirm");
    btn.textContent = "¿Confirmar?";
    if (state.confirmTimers[scope]) clearTimeout(state.confirmTimers[scope]);
    state.confirmTimers[scope] = setTimeout(() => {
      delete btn.dataset.confirmPending;
      btn.classList.remove("arm-btn-confirm");
      btn.textContent = defaultLabel;
      delete state.confirmTimers[scope];
    }, 3800);
  }

  function restoreModalFocus() {
    const prev = state.lastFocusedEl;
    state.lastFocusedEl = null;
    if (prev && typeof prev.focus === "function" && document.contains(prev)) {
      prev.focus();
    }
  }

  function closeCompareModal(restoreFocus = false) {
    if (!el.compareModal.classList.contains("open")) return;
    el.compareModal.classList.remove("open");
    el.compareModal.setAttribute("aria-hidden", "true");
    syncModalLock();
    if (restoreFocus) restoreModalFocus();
  }

  function closeLogModal(restoreFocus = false) {
    if (!el.logModal.classList.contains("open")) return;
    resetConfirmButtons();
    el.logModal.classList.remove("open");
    el.logModal.setAttribute("aria-hidden", "true");
    syncModalLock();
    if (restoreFocus) restoreModalFocus();
  }

  async function openCompareModal() {
    const switchingFromLog = el.logModal.classList.contains("open");
    if (!switchingFromLog) {
      state.lastFocusedEl = document.activeElement;
    } else {
      closeLogModal(false);
    }

    el.compareModal.classList.add("open");
    el.compareModal.setAttribute("aria-hidden", "false");
    if (el.compareBody) el.compareBody.scrollTop = 0;
    syncModalLock();
    requestAnimationFrame(() => {
      if (el.compareClose) el.compareClose.focus();
    });

    const myCmpSeq = ++state.compareReqSeq;
    el.compareCards.innerHTML = `<p class="sv-pane-intro">Ejecutando la tarea completa con las 5 estrategias en Python...</p>`;
    el.compareSummary.textContent = "";
    el.compareSummary.hidden = true;

    try {
      const resp = await fetch("/api/arm/compare-sequence", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          start_deg: state.startDeg,
          waypoints: state.waypoints,
          obstacles: getActiveObstaclesList(),
          cargo_id: state.cargoId
        })
      });
      const json = await resp.json();
      if (myCmpSeq !== state.compareReqSeq) return;
      if (json.status !== "success") {
        el.compareCards.innerHTML = `<p class="sv-pane-intro">${escapeHtml(json.message || "No se pudo completar la comparativa.")}</p>`;
        return;
      }

      const rows = json.data.comparisons;
      const maxExp = Math.max(...rows.map((r) => r.nodes_expanded), 1);
      const maxEn = Math.max(...rows.map((r) => r.energy || 0), 1);

      el.compareCards.innerHTML = rows.map((row) => {
        const expPct = row.nodes_expanded > 0 ? Math.max(4, Math.round((row.nodes_expanded / maxExp) * 100)) : 0;
        const enPct = row.found ? Math.max(4, Math.round((row.energy / maxEn) * 100)) : 100;

        const outcome = classifyRunOutcome(row);
        const isCurrent = row.algorithm_id === state.algorithm;
        const cardCls = [
          outcome.kind === "fail"
            ? "is-failed"
            : (outcome.kind === "optimal" && row.algorithm_id === "astar")
              ? "is-winner"
              : "",
          isCurrent ? "is-current" : ""
        ].filter(Boolean).join(" ");

        const badgeLabel = outcome.kind === "fail"
          ? `Fallo (${row.completed_stages}/${row.total_stages})`
          : outcome.kind === "optimal"
            ? `Optima · ${row.cycle_seconds} s`
            : outcome.kind === "over_budget"
              ? `Fuera exp. (&gt;${outcome.budgetLimit})`
              : `Rodeo · ${row.cycle_seconds} s`;
        const badgeHtml = `<span class="arm-cmp-badge ${outcome.badgeTone}">${badgeLabel}</span>`;
        const activeTag = isCurrent ? `<span class="arm-cmp-active-tag">Activa</span>` : "";

        return `
          <button type="button" class="arm-cmp-card ${cardCls}" data-pick-algo="${escapeHtml(row.algorithm_id)}" title="Aplicar ${escapeHtml(row.algorithm_name)} en la celda 3D">
            <div class="arm-cmp-top">
              <span class="arm-cmp-title-wrap">
                <span class="arm-cmp-name">${escapeHtml(row.algorithm_name)}</span>
                ${activeTag}
              </span>
              ${badgeHtml}
            </div>
            <div class="arm-cmp-bars">
              <div class="arm-bar-row">
                <div class="arm-bar-head">
                  <span>Posturas probadas</span>
                  <strong>${row.nodes_expanded}</strong>
                </div>
                <div class="arm-bar-track"><div class="arm-bar-fill ${row.found ? "" : "is-fail"}" style="width:${expPct}%"></div></div>
              </div>
              <div class="arm-bar-row">
                <div class="arm-bar-head">
                  <span>Energia gastada</span>
                  <strong>${row.found ? row.energy : "Detenido"}</strong>
                </div>
                <div class="arm-bar-track"><div class="arm-bar-fill ${row.found ? "is-alt" : "is-fail"}" style="width:${enPct}%"></div></div>
              </div>
            </div>
          </button>
        `;
      }).join("");

      el.compareCards.querySelectorAll("[data-pick-algo]").forEach((btn) => {
        btn.addEventListener("click", () => {
          const picked = btn.dataset.pickAlgo;
          closeCompareModal(false);
          selectAlgorithm(picked, true);
        });
      });

      const astar = rows.find((r) => r.algorithm_id === "astar");
      const ucs = rows.find((r) => r.algorithm_id === "ucs");
      const failed = rows.filter((r) => !r.found).map((r) => r.algorithm_name);
      const overBudget = rows
        .filter((r) => classifyRunOutcome(r).kind === "over_budget")
        .map((r) => r.algorithm_name);
      const budgetLimit = (astar && astar.budget_limit) || 900;

      if (astar && ucs && astar.found) {
        const failText = failed.length ? ` No logro terminar: ${failed.join(", ")}.` : "";
        const budgetText = overBudget.length ? ` Fuera de expectativas (>${budgetLimit} posturas): ${overBudget.join(", ")}.` : "";
        el.compareSummary.textContent =
          `Resumen de produccion: A* completo la tarea en ${astar.cycle_seconds} s con energia minima (${astar.energy}) ` +
          `probando ${astar.nodes_expanded} posturas, frente a ${ucs.nodes_expanded} de Costo Uniforme.${budgetText}${failText}`;
      } else {
        el.compareSummary.textContent = "Con los obstaculos actuales no es posible completar la secuencia.";
      }
      el.compareSummary.hidden = false;
    } catch (err) {
      if (myCmpSeq !== state.compareReqSeq) return;
      el.compareCards.innerHTML = `<p class="sv-pane-intro">Error al comparar estrategias en Python.</p>`;
      el.compareSummary.hidden = true;
    }
  }

  // =========================================================================
  // BITACORA SQL, MEMORIA DE RUTAS (CBR) Y MINI-RAG LOCAL
  // =========================================================================
  async function refreshHistoryBadge() {
    try {
      const resp = await fetch("/api/arm/history?summary_only=1");
      const json = await resp.json();
      if (json.status === "success" && el.historyCount) {
        el.historyCount.textContent = String(json.data.kpis.total_runs || 0);
      }
    } catch (err) {
      // Silencioso si aun no esta disponible
    }
  }

  function switchLogTab(tabName) {
    resetConfirmButtons();
    el.logTabs.forEach((t) => {
      const active = t.dataset.armTab === tabName;
      t.classList.toggle("active", active);
      t.setAttribute("aria-selected", active ? "true" : "false");
      if (active && typeof t.scrollIntoView === "function") {
        t.scrollIntoView({ behavior: "smooth", inline: "center", block: "nearest" });
      }
    });
    el.logPanes.forEach((p) => {
      const active = p.dataset.armPane === tabName;
      p.classList.toggle("active", active);
      p.hidden = !active;
      if (active) {
        p.scrollTop = 0;
        const scrollEl = p.querySelector(".arm-modal-scroll");
        if (scrollEl) scrollEl.scrollTop = 0;
      }
    });
    if ((tabName === "history" || tabName === "cargo" || tabName === "memory") &&
        (state.historyDirty || state.historyLoadedFilter !== state.sqlFilter)) {
      loadHistoryData(false);
    }
  }

  async function openLogModal() {
    const switchingFromCompare = el.compareModal.classList.contains("open");
    if (!switchingFromCompare) {
      state.lastFocusedEl = document.activeElement;
    } else {
      closeCompareModal(false);
    }

    el.logModal.classList.add("open");
    el.logModal.setAttribute("aria-hidden", "false");
    syncModalLock();
    requestAnimationFrame(() => {
      const activeTab = el.logModal.querySelector(".arm-log-tabs .modal-tab-item.active");
      if (activeTab) activeTab.focus();
      else if (el.logClose) el.logClose.focus();
    });

    if (state.historyDirty || state.historyLoadedFilter !== state.sqlFilter) {
      await loadHistoryData(false);
    }
  }

  async function loadHistoryData(force = true) {
    if (!force && !state.historyDirty && state.historyLoadedFilter === state.sqlFilter) return;
    const mySeq = ++state.historyReqSeq;
    const requestedFilter = state.sqlFilter;

    try {
      const resp = await fetch(`/api/arm/history?filter=${encodeURIComponent(requestedFilter)}&limit=40`);
      const json = await resp.json();
      if (mySeq !== state.historyReqSeq) return;
      if (json.status !== "success") {
        el.runsList.innerHTML = `<p class="sv-pane-intro">No se pudo consultar la bitacora SQL.</p>`;
        return;
      }

      const { kpis, runs, cargo_ledger: cargoLedger, cache_entries: cacheEntries } = json.data;
      state.historyDirty = false;
      state.historyLoadedFilter = requestedFilter;

      if (el.historyCount) el.historyCount.textContent = String(kpis.total_runs);
      el.sqlTotal.textContent = String(kpis.total_runs);
      el.sqlFailures.textContent = String(kpis.total_failures);
      el.sqlCached.textContent = String(kpis.total_from_cache);
      el.sqlSavings.textContent = kpis.astar_energy_savings_pct !== null ? `${kpis.astar_energy_savings_pct}%` : "—";

      if (el.cargoDelivered) el.cargoDelivered.textContent = String(kpis.total_deliveries || 0);
      if (el.cargoKg) el.cargoKg.textContent = `${kpis.total_kg_delivered || 0} kg`;
      if (el.cargoMeters) el.cargoMeters.textContent = `${kpis.total_distance_m || 0} m`;
      if (el.cargoAborted) el.cargoAborted.textContent = String(kpis.aborted_transports || 0);

      renderRunsList(runs);
      renderCargoList(cargoLedger || []);
      renderCacheList(cacheEntries);
    } catch (err) {
      if (mySeq !== state.historyReqSeq) return;
      el.runsList.innerHTML = `<p class="sv-pane-intro">No se pudo cargar la bitacora SQL.</p>`;
    }
  }

  function renderRunsList(runs) {
    if (!runs || !runs.length) {
      el.runsList.innerHTML = `<p class="sv-pane-intro">No hay registros para este filtro todavia.</p>`;
      return;
    }

    el.runsList.innerHTML = runs.map((r) => {
      const outcome = classifyRunOutcome(r);
      const tagText = outcome.kind === "fail"
        ? `Fallo (${r.completed_stages}/${r.total_stages})`
        : outcome.kind === "optimal"
          ? `Optima · ${r.cycle_seconds} s`
          : outcome.kind === "over_budget"
            ? `Fuera exp. · ${r.cycle_seconds} s`
            : `Rodeo · ${r.cycle_seconds} s`;
      const memTag = r.from_cache ? `<span class="arm-run-tag is-ok">Memoria SQL</span>` : "";
      const unexpTag = r.had_unexpected ? `<span class="arm-run-tag is-warn">Imprevisto</span>` : "";
      const budgetTag = outcome.kind === "over_budget"
        ? `<span class="arm-run-tag is-warn">&gt;${outcome.budgetLimit} exp.</span>`
        : "";
      const cargoLabel = r.cargo_name ? `${escapeHtml(r.cargo_name)} (${r.weight_kg || 18} kg)` : "";
      const cargoTag = cargoLabel
        ? `<span class="arm-run-tag ${r.delivered ? "is-ok" : "is-fail"}">${cargoLabel}</span>`
        : "";

      return `
        <div class="arm-run-card">
          <div class="arm-run-main">
            <div class="arm-run-title">
              <span>#${r.id} · ${escapeHtml(r.task_name)}</span>
              <span class="arm-run-tag ${outcome.tone}">${tagText}</span>
              ${cargoTag}
              ${budgetTag}
              ${memTag}
              ${unexpTag}
            </div>
            <div class="arm-run-meta">
              <strong>${escapeHtml(r.algorithm_name)}</strong> · ${r.nodes_expanded} posturas · Energia ${r.energy}${r.payload_energy_tax ? ` (+${r.payload_energy_tax} por peso)` : ""}
              ${r.reason ? `<br><em>${escapeHtml(r.reason)}</em>` : ""}
            </div>
          </div>
          <button type="button" class="arm-run-replay" data-replay-run="${r.id}">Cargar escena</button>
        </div>
      `;
    }).join("");

    el.runsList.querySelectorAll("[data-replay-run]").forEach((btn) => {
      const runObj = runs.find((item) => String(item.id) === btn.dataset.replayRun);
      if (!runObj) return;
      btn.addEventListener("click", () => replaySavedScene(runObj));
    });
  }

  function renderCargoList(ledger) {
    if (!el.cargoList) return;
    if (!ledger || !ledger.length) {
      el.cargoList.innerHTML = `<p class="sv-pane-intro">Aun no hay traslados de carga registrados en <code>arm_cargo_ledger</code>.</p>`;
      return;
    }

    el.cargoList.innerHTML = ledger.map((item) => {
      const statusCls = item.delivered ? "is-ok" : item.picked_up ? "is-warn" : "is-fail";
      const statusText = item.delivered
        ? "Entregada en destino"
        : item.picked_up
          ? "Abortada en transito"
          : "Sin recoger en origen";

      return `
        <div class="arm-run-card">
          <div class="arm-run-main">
            <div class="arm-run-title">
              <span>Lote #${item.id} · ${escapeHtml(item.cargo_name)} (${item.weight_kg} kg)</span>
              <span class="arm-run-tag ${statusCls}">${statusText}</span>
              <span class="arm-run-tag">${escapeHtml(item.algorithm_name)}</span>
            </div>
            <div class="arm-run-meta">
              Ruta: <strong>${escapeHtml(item.origin_station)}</strong> &rarr; <strong>${escapeHtml(item.destination_station)}</strong>
              &middot; Recorrido con carga: <strong>${item.transport_distance_m} m</strong>
              &middot; Energia: ${item.base_energy} base + <strong>${item.payload_energy_tax} por torque</strong> (Total ${item.total_loaded_energy})
            </div>
          </div>
        </div>
      `;
    }).join("");
  }

  function renderCacheList(entries) {
    if (!entries || !entries.length) {
      el.cacheList.innerHTML = `<p class="sv-pane-intro">La memoria SQL esta vacia. Ejecuta una tarea exitosa para recordarla.</p>`;
      return;
    }
    el.cacheList.innerHTML = entries.map((c) => `
      <div class="arm-run-card">
        <div class="arm-run-main">
          <div class="arm-run-title">
            <span>${escapeHtml(c.task_name)}</span>
            <span class="arm-run-tag is-ok">${escapeHtml(c.algorithm_id.toUpperCase())}</span>
            <span class="arm-run-tag">Reutilizada ${c.hit_count}x</span>
          </div>
          <div class="arm-run-meta">
            Huella <code>${escapeHtml(c.scene_hash)}</code> · Energia ${c.energy} · Ciclo ${c.cycle_seconds} s
          </div>
        </div>
      </div>
    `).join("");
  }

  function replaySavedScene(runObj) {
    const sc = runObj.scene;
    if (!sc || !sc.waypoints) return;

    state.activeTaskId = sc.task_id || state.activeTaskId;
    state.algorithm = sc.algorithm_id || runObj.algorithm_id;
    state.cargoId = sc.cargo_id || runObj.cargo_id || state.cargoId;
    if (el.cargoSelect) el.cargoSelect.value = state.cargoId;
    state.startDeg = [...(sc.start_deg || [170, 15])];
    state.waypoints = sc.waypoints.map((w) => ({ ...w }));
    state.unexpectedActive = Boolean(sc.had_unexpected);
    const allObs = (sc.obstacles || []).map((o) => ({ ...o }));
    state.obstacles = allObs.filter((o) => o.id !== "obs_emergency");
    const emerg = allObs.find((o) => o.id === "obs_emergency");
    const presetTask = state.meta && state.meta.tasks.find((t) => t.id === state.activeTaskId);
    state.unexpectedSpec = emerg || (presetTask && presetTask.unexpected ? { ...presetTask.unexpected } : state.unexpectedSpec);

    el.presetButtons.querySelectorAll(".arm-preset-btn").forEach((b) => {
      b.classList.toggle("active", b.dataset.task === state.activeTaskId);
    });
    selectAlgorithm(state.algorithm, false);
    el.btnEmergency.classList.toggle("active", state.unexpectedActive);
    el.btnEmergency.textContent = state.unexpectedActive ? "Quitar imprevisto" : "Imprevisto";

    closeLogModal(false);
    refreshCarriedCargoMesh();
    rebuildThreeObstaclesAndWaypoints();
    runPythonSequence();
  }

  async function runRagQuery(question) {
    const q = String(question || "").trim();
    if (!q) return;
    const mySeq = ++state.ragReqSeq;
    el.ragAnswer.textContent = "Consultando registros en SQLite...";
    if (el.ragSubmit) el.ragSubmit.disabled = true;

    try {
      const resp = await fetch("/api/arm/rag", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q })
      });
      const json = await resp.json();
      if (mySeq !== state.ragReqSeq) return;
      if (json.status !== "success") {
        el.ragAnswer.textContent = json.message || "No se pudo completar la consulta en SQLite.";
        el.ragSources.innerHTML = "";
        return;
      }

      const rag = json.data;
      el.ragAnswer.textContent = rag.answer;

      if (!rag.sources || !rag.sources.length) {
        el.ragSources.innerHTML = "";
        return;
      }
      el.ragSources.innerHTML = rag.sources.map((s) => `
        <div class="arm-run-card">
          <div class="arm-run-main">
            <div class="arm-run-title">
              <span>Fuente SQL #${s.id} · ${escapeHtml(s.task_name)}</span>
              <span class="arm-run-tag ${s.found ? "is-ok" : "is-fail"}">${s.found ? "Exito" : "Fallo"}</span>
              <span class="arm-run-tag">Similitud ${(s.rag_score * 100).toFixed(0)}%</span>
            </div>
            <div class="arm-run-meta">
              ${escapeHtml(s.algorithm_name)} · Energia ${s.energy} · ${s.nodes_expanded} posturas · Ciclo ${s.cycle_seconds} s
            </div>
          </div>
        </div>
      `).join("");
    } catch (err) {
      if (mySeq !== state.ragReqSeq) return;
      el.ragAnswer.textContent = "Error al consultar el Mini-RAG en Python.";
      el.ragSources.innerHTML = "";
    } finally {
      if (mySeq === state.ragReqSeq && el.ragSubmit) {
        el.ragSubmit.disabled = false;
      }
    }
  }

  async function clearStorage(scope) {
    try {
      const resp = await fetch(`/api/arm/history?scope=${encodeURIComponent(scope)}`, { method: "DELETE" });
      if (!resp.ok) return;
      state.historyDirty = true;
      if (scope === "runs" || scope === "all") {
        el.ragAnswer.textContent = "Historial limpiado. Ejecuta una tarea en la celda 3D y vuelve a consultar.";
        el.ragSources.innerHTML = "";
        el.ragChips.forEach((c) => c.classList.remove("active"));
      }
      await loadHistoryData(true);
    } catch (err) {
      el.runsList.innerHTML = `<p class="sv-pane-intro">No se pudo limpiar el almacenamiento SQL.</p>`;
    }
  }

  init();
});
