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
    speedBtns: card.querySelectorAll(".arm-speed-btn"),
    camBtns: card.querySelectorAll(".arm-cam-btn"),
    container3d: document.getElementById("arm3dContainer"),
    hoverHud: document.getElementById("armHoverHud"),
    csCanvas: document.getElementById("armCspaceCanvas"),
    statExpanded: document.getElementById("armStatExpanded"),
    statEnergy: document.getElementById("armStatEnergy"),
    statStatus: document.getElementById("armStatStatus"),
    kpiStatusBox: document.getElementById("armKpiStatusBox"),
    verdictBox: document.getElementById("armVerdictBox"),
    verdictText: document.getElementById("armVerdictText"),
    compareModal: document.getElementById("armCompareModal"),
    compareClose: document.getElementById("armCompareClose"),
    compareCards: document.getElementById("armCompareCards"),
    compareSummary: document.getElementById("armCompareSummary"),
    logModal: document.getElementById("armLogModal"),
    logClose: document.getElementById("armLogClose"),
    logTabs: document.querySelectorAll("#armLogModal [data-arm-tab]"),
    logPanes: document.querySelectorAll("#armLogModal [data-arm-pane]"),
    ragChips: document.querySelectorAll("#armLogModal [data-rag-q]"),
    ragForm: document.getElementById("armRagForm"),
    ragInput: document.getElementById("armRagInput"),
    ragAnswer: document.getElementById("armRagAnswer"),
    ragSources: document.getElementById("armRagSources"),
    sqlTotal: document.getElementById("armSqlTotal"),
    sqlFailures: document.getElementById("armSqlFailures"),
    sqlCached: document.getElementById("armSqlCached"),
    sqlSavings: document.getElementById("armSqlSavings"),
    sqlFilters: document.querySelectorAll("#armLogModal [data-sql-filter]"),
    btnClearRuns: document.getElementById("armBtnClearRuns"),
    runsList: document.getElementById("armRunsList"),
    toggleMemory: document.getElementById("armToggleMemory"),
    btnClearCache: document.getElementById("armBtnClearCache"),
    cacheList: document.getElementById("armCacheList")
  };

  const csCtx = el.csCanvas.getContext("2d");

  const state = {
    meta: null,
    activeTaskId: "pick_and_place",
    algorithm: "astar",
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
    carryingPart: false,
    speed: 1.0,
    paused: false,
    phase: "idle", // 'exploring' | 'moving' | 'done' | 'failed'
    expCursor: 0,
    pathCursor: 0,
    liveDeg: [170, 15],
    cspaceHover: null, // { i1, i2, val }
    lastTickTime: 0,
    rafId: null
  };

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
    carriedPartMesh: null,
    floorPartMesh: null,
    waypointGroups: [],
    trailLine: null,
    sparkPoints: null,
    sparkVel: [],
    sparksActive: false,
    shockwaveRing: null,
    shockwaveScale: 0,
    obstacleGroups: [],
    dragTarget: null,
    raycaster: null,
    floorPlane: null,
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

  async function init() {
    try {
      const resp = await fetch("/api/arm/presets");
      const json = await resp.json();
      if (json.status !== "success") return;

      state.meta = json.data;
      renderPresetButtons();
      loadTask("pick_and_place", false);
      initThreeScene();
      bindEvents();
      await runPythonSequence();
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

  function loadTask(taskId, solveNow = true) {
    const task = state.meta.tasks.find((t) => t.id === taskId) || state.meta.tasks[0];
    state.activeTaskId = task.id;
    state.startDeg = [...task.start_deg];
    state.liveDeg = [...task.start_deg];
    state.waypoints = task.waypoints.map((w) => ({ ...w }));
    state.obstacles = task.obstacles.map((o) => ({ ...o }));
    state.unexpectedSpec = task.unexpected ? { ...task.unexpected } : null;
    state.unexpectedActive = false;
    state.carryingPart = false;
    state.completedWaypoints = 0;

    el.btnEmergency.classList.remove("active");
    el.btnEmergency.textContent = "Obstaculo imprevisto";
    el.presetButtons.querySelectorAll(".arm-preset-btn").forEach((b) => {
      b.classList.toggle("active", b.dataset.task === task.id);
    });

    if (three.ready) rebuildThreeObstaclesAndWaypoints();
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

  // =========================================================================
  // ESCENA 3D EN THREE.JS
  // =========================================================================
  function initThreeScene() {
    if (typeof window.THREE === "undefined") {
      el.container3d.innerHTML = `<p style="padding:20px;text-align:center;">No se pudo cargar Three.js.</p>`;
      return;
    }

    const THREE = window.THREE;
    const w = el.container3d.clientWidth || 560;
    const h = el.container3d.clientHeight || 416;

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

    const camHud = el.container3d.querySelector(".arm-cam-hud");
    const hoverHud = el.hoverHud;
    el.container3d.innerHTML = "";
    el.container3d.appendChild(three.renderer.domElement);
    if (camHud) el.container3d.appendChild(camHud);
    if (hoverHud) el.container3d.appendChild(hoverHud);

    three.raycaster = new THREE.Raycaster();
    three.floorPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);

    const hemi = new THREE.HemisphereLight(0xf8fafc, 0x334155, 0.85);
    three.scene.add(hemi);

    const keyLight = new THREE.DirectionalLight(0xfffbeb, 1.35);
    keyLight.position.set(6, 13, 8);
    keyLight.castShadow = true;
    keyLight.shadow.mapSize.set(2048, 2048);
    keyLight.shadow.bias = -0.0005;
    const d = 9.5;
    keyLight.shadow.camera.left = -d;
    keyLight.shadow.camera.right = d;
    keyLight.shadow.camera.top = d;
    keyLight.shadow.camera.bottom = -d;
    three.scene.add(keyLight);

    const rimLight = new THREE.DirectionalLight(0x5fb3a2, 0.55);
    rimLight.position.set(-7, 6, -6);
    three.scene.add(rimLight);

    const floorMat = new THREE.MeshStandardMaterial({
      map: isDarkTheme() ? three.textures.floorDark : three.textures.floorLight,
      roughness: 0.72,
      metalness: 0.12
    });
    const floor = new THREE.Mesh(new THREE.PlaneGeometry(24, 24), floorMat);
    floor.rotation.x = -Math.PI / 2;
    floor.receiveShadow = true;
    three.scene.add(floor);
    three.floorMesh = floor;

    updateSceneTheme();

    const reach = L1_3D + L2_3D;
    const reachRing = new THREE.Mesh(
      new THREE.RingGeometry(reach - 0.045, reach + 0.045, 72),
      new THREE.MeshBasicMaterial({ color: 0x4f8c82, side: THREE.DoubleSide, transparent: true, opacity: 0.5 })
    );
    reachRing.rotation.x = -Math.PI / 2;
    reachRing.position.y = 0.015;
    three.scene.add(reachRing);

    buildThreeRobot();
    buildThreeGhostRobot();
    buildThreeEffects();
    rebuildThreeObstaclesAndWaypoints();

    const ro = new ResizeObserver(() => {
      const nw = el.container3d.clientWidth;
      const nh = el.container3d.clientHeight;
      if (nw > 10 && nh > 10 && three.renderer) {
        three.camera.aspect = nw / nh;
        three.camera.updateProjectionMatrix();
        three.renderer.setSize(nw, nh);
      }
    });
    ro.observe(el.container3d);

    three.ready = true;
    startRenderLoop();
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

  function buildThreeRobot() {
    const THREE = window.THREE;
    const armY = 1.12;
    const steelDark = new THREE.MeshStandardMaterial({ color: 0x26323d, roughness: 0.4, metalness: 0.72 });
    const chromeMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, roughness: 0.25, metalness: 0.85 });
    const tealMat = new THREE.MeshStandardMaterial({ color: 0x2f6f63, roughness: 0.32, metalness: 0.5 });
    const goldMat = new THREE.MeshStandardMaterial({ color: 0xc98a3e, roughness: 0.32, metalness: 0.5 });

    const basePlate = new THREE.Mesh(new THREE.CylinderGeometry(0.75, 0.82, 0.1, 32), steelDark);
    basePlate.position.y = 0.05;
    basePlate.receiveShadow = true;
    basePlate.castShadow = true;
    three.scene.add(basePlate);

    for (let b = 0; b < 6; b++) {
      const ang = (b * Math.PI) / 3;
      const bolt = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.06, 6), chromeMat);
      bolt.position.set(Math.cos(ang) * 0.62, 0.11, Math.sin(ang) * 0.62);
      three.scene.add(bolt);
    }

    const pedestal = new THREE.Mesh(new THREE.CylinderGeometry(0.42, 0.56, armY - 0.1, 28), steelDark);
    pedestal.position.y = 0.1 + (armY - 0.1) / 2;
    pedestal.castShadow = true;
    three.scene.add(pedestal);

    const glowRing = new THREE.Mesh(
      new THREE.TorusGeometry(0.44, 0.032, 12, 36),
      new THREE.MeshBasicMaterial({ color: 0x4fd1c5 })
    );
    glowRing.rotation.x = Math.PI / 2;
    glowRing.position.y = 0.24;
    three.scene.add(glowRing);

    three.shoulderGroup = new THREE.Group();
    three.shoulderGroup.position.set(0, armY, 0);
    three.scene.add(three.shoulderGroup);

    three.shoulderGroup.add(new THREE.Mesh(new THREE.CylinderGeometry(0.32, 0.34, 0.42, 24), steelDark));
    three.shoulderGroup.add(new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.22, 0.46, 20), chromeMat));

    const link1Body = new THREE.Mesh(new THREE.BoxGeometry(L1_3D, 0.24, 0.32), tealMat);
    link1Body.position.x = L1_3D / 2;
    link1Body.castShadow = true;
    three.shoulderGroup.add(link1Body);

    const link1Stripe = new THREE.Mesh(new THREE.BoxGeometry(L1_3D * 0.78, 0.05, 0.34), chromeMat);
    link1Stripe.position.set(L1_3D / 2, 0.11, 0);
    three.shoulderGroup.add(link1Stripe);

    three.elbowGroup = new THREE.Group();
    three.elbowGroup.position.set(L1_3D, 0.18, 0);
    three.shoulderGroup.add(three.elbowGroup);

    three.elbowGroup.add(new THREE.Mesh(new THREE.CylinderGeometry(0.24, 0.25, 0.36, 24), steelDark));
    three.elbowGroup.add(new THREE.Mesh(new THREE.CylinderGeometry(0.15, 0.15, 0.4, 18), chromeMat));

    const link2Body = new THREE.Mesh(new THREE.BoxGeometry(L2_3D, 0.18, 0.24), goldMat);
    link2Body.position.x = L2_3D / 2;
    link2Body.castShadow = true;
    three.elbowGroup.add(link2Body);

    const torchCollar = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.10, 0.28, 16), steelDark);
    torchCollar.position.set(L2_3D, -0.05, 0);
    three.elbowGroup.add(torchCollar);

    const torchNozzle = new THREE.Mesh(new THREE.CylinderGeometry(0.075, 0.03, 0.78, 16), chromeMat);
    torchNozzle.position.set(L2_3D, -0.55, 0);
    torchNozzle.castShadow = true;
    three.elbowGroup.add(torchNozzle);

    const copperTip = new THREE.Mesh(
      new THREE.SphereGeometry(0.075, 14, 14),
      new THREE.MeshBasicMaterial({ color: 0xfbbf24 })
    );
    copperTip.position.set(L2_3D, -0.96, 0);
    three.elbowGroup.add(copperTip);

    // Pieza metalica agarrada por el brazo durante Pick & Place
    three.carriedPartMesh = new THREE.Mesh(
      new THREE.BoxGeometry(0.46, 0.22, 0.46),
      new THREE.MeshStandardMaterial({ color: 0x38bdf8, metalness: 0.7, roughness: 0.25, emissive: 0x0284c7, emissiveIntensity: 0.35 })
    );
    three.carriedPartMesh.position.set(L2_3D, -1.06, 0);
    three.carriedPartMesh.castShadow = true;
    three.carriedPartMesh.visible = false;
    three.elbowGroup.add(three.carriedPartMesh);

    three.torchLight = new THREE.PointLight(0xfbbf24, 0.0, 4.5);
    three.torchLight.position.set(L2_3D, -1.0, 0);
    three.elbowGroup.add(three.torchLight);
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

  function updateTrail3D(frames) {
    const THREE = window.THREE;
    if (three.trailLine) {
      three.scene.remove(three.trailLine);
      three.trailLine.geometry.dispose();
      three.trailLine = null;
    }
    if (!frames || frames.length < 2) return;

    const pts = frames.map((f) => {
      const p3 = to3D(f.tx, f.ty);
      return new THREE.Vector3(p3.x, 0.34, p3.z);
    });
    const geo = new THREE.BufferGeometry().setFromPoints(pts);
    three.trailLine = new THREE.Line(
      geo,
      new THREE.LineBasicMaterial({ color: 0xe0ae63, transparent: true, opacity: 0.85 })
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
      const leg = new THREE.Mesh(
        new THREE.BoxGeometry(w3 * 0.86, 0.28, d3 * 0.78),
        new THREE.MeshStandardMaterial({ color: 0x334155, metalness: 0.7, roughness: 0.4 })
      );
      leg.position.y = 0.14;
      addPart(leg);

      const body = new THREE.Mesh(
        new THREE.BoxGeometry(w3, 0.86, d3),
        new THREE.MeshStandardMaterial({ color: 0x3b6998, metalness: 0.55, roughness: 0.28 })
      );
      body.position.y = 0.71;
      addPart(body);

      const win = new THREE.Mesh(
        new THREE.BoxGeometry(w3 * 0.78, 0.36, d3 * 1.02),
        new THREE.MeshStandardMaterial({ color: 0x111827, metalness: 0.8, roughness: 0.15 })
      );
      win.position.y = 0.94;
      addPart(win);
    } else if (ob.kind === "press") {
      const isEmergency = ob.id === "obs_emergency";
      const base = new THREE.Mesh(
        new THREE.BoxGeometry(w3, 0.24, d3),
        new THREE.MeshStandardMaterial({ map: three.textures.hazardYellow, roughness: 0.6 })
      );
      base.position.y = 0.12;
      addPart(base);

      const frame = new THREE.Mesh(
        new THREE.BoxGeometry(w3 * 0.94, isEmergency ? 0.9 : 1.32, d3 * 0.94),
        new THREE.MeshStandardMaterial({ color: isEmergency ? 0xef4444 : 0xd97706, roughness: 0.42, metalness: 0.35 })
      );
      frame.position.y = isEmergency ? 0.69 : 0.90;
      addPart(frame);

      if (!isEmergency) {
        const crown = new THREE.Mesh(
          new THREE.BoxGeometry(w3 * 0.72, 0.28, d3 * 0.72),
          new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.45, metalness: 0.65 })
        );
        crown.position.y = 1.70;
        addPart(crown);
      }
    } else if (ob.kind === "pillar") {
      const collar = new THREE.Mesh(
        new THREE.BoxGeometry(w3 * 1.04, 0.36, d3 * 1.04),
        new THREE.MeshStandardMaterial({ map: three.textures.hazardRed, roughness: 0.6 })
      );
      collar.position.y = 0.18;
      addPart(collar);

      const col = new THREE.Mesh(
        new THREE.BoxGeometry(w3 * 0.92, 1.78, d3 * 0.92),
        new THREE.MeshStandardMaterial({ color: 0x64748b, roughness: 0.72, metalness: 0.2 })
      );
      col.position.y = 1.25;
      addPart(col);
    } else {
      const frame = new THREE.Mesh(
        new THREE.BoxGeometry(w3, 0.32, d3 * 0.92),
        new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.5, metalness: 0.6 })
      );
      frame.position.y = 0.46;
      addPart(frame);

      const belt = new THREE.Mesh(
        new THREE.BoxGeometry(w3 * 0.96, 0.08, d3 * 0.78),
        new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.9 })
      );
      belt.position.y = 0.65;
      addPart(belt);

      const rollerMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, metalness: 0.8, roughness: 0.25 });
      const steps = Math.max(3, Math.floor(w3 * 2));
      for (let r = 0; r < steps; r++) {
        const rx = -w3 * 0.42 + (r / (steps - 1)) * (w3 * 0.84);
        const roller = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.07, d3 * 0.98, 12), rollerMat);
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

  function rebuildThreeObstaclesAndWaypoints() {
    if (!three.scene || !window.THREE) return;
    const THREE = window.THREE;

    three.obstacleGroups.forEach((g) => three.scene.remove(g));
    three.obstacleGroups = [];

    const allObs = getActiveObstaclesList();
    allObs.forEach((ob, idx) => {
      const grp = createObstacleGroup(ob, idx);
      three.scene.add(grp);
      three.obstacleGroups.push(grp);
    });

    three.waypointGroups.forEach((g) => three.scene.remove(g));
    three.waypointGroups = [];
    if (three.floorPartMesh) {
      three.scene.remove(three.floorPartMesh);
      three.floorPartMesh = null;
    }

    state.waypoints.forEach((wp, idx) => {
      const grp = new THREE.Group();
      const pos3 = to3D(wp.x, wp.y);
      grp.position.set(pos3.x, 0.02, pos3.z);

      const colorHex = wp.action === "pick" ? 0x38bdf8 : wp.action === "place" ? 0xa855f7 : 0xef4444;

      const pad = new THREE.Mesh(
        new THREE.CylinderGeometry(0.35, 0.39, 0.08, 24),
        new THREE.MeshStandardMaterial({ color: 0x334155, metalness: 0.7, roughness: 0.3 })
      );
      pad.position.y = 0.04;
      pad.userData = { dragType: "waypoint", index: idx, label: wp.label, parentGroup: grp };
      grp.add(pad);

      const ring = new THREE.Mesh(
        new THREE.TorusGeometry(0.37, 0.045, 12, 32),
        new THREE.MeshBasicMaterial({ color: colorHex })
      );
      ring.rotation.x = Math.PI / 2;
      ring.position.y = 0.08;
      ring.userData = { dragType: "waypoint", index: idx, label: wp.label, parentGroup: grp };
      grp.add(ring);

      const beacon = new THREE.Mesh(
        new THREE.CylinderGeometry(0.07, 0.13, 0.28, 16),
        new THREE.MeshStandardMaterial({ color: colorHex, emissive: colorHex, emissiveIntensity: 0.4 })
      );
      beacon.position.y = 0.20;
      beacon.userData = { dragType: "waypoint", index: idx, label: wp.label, parentGroup: grp };
      grp.add(beacon);

      grp.userData = { ring, beacon, defaultColor: colorHex };
      three.scene.add(grp);
      three.waypointGroups.push(grp);

      // Si es Pick & Place, mostrar la pieza esperando en la banda (wp_pick)
      if (wp.action === "pick") {
        three.floorPartMesh = new THREE.Mesh(
          new THREE.BoxGeometry(0.46, 0.22, 0.46),
          new THREE.MeshStandardMaterial({ color: 0x38bdf8, metalness: 0.7, roughness: 0.25, emissive: 0x0284c7, emissiveIntensity: 0.35 })
        );
        three.floorPartMesh.position.set(pos3.x, 0.22, pos3.z);
        three.floorPartMesh.castShadow = true;
        three.scene.add(three.floorPartMesh);
      }
    });
  }

  function updateWaypointVisuals(completedCount) {
    three.waypointGroups.forEach((grp, idx) => {
      const done = idx < completedCount;
      const colorHex = done ? 0x22c55e : grp.userData.defaultColor;
      grp.userData.ring.material.color.setHex(colorHex);
      grp.userData.beacon.material.color.setHex(colorHex);
      grp.userData.beacon.material.emissive.setHex(colorHex);
    });
  }

  function setRobotAnglesDeg(deg1, deg2) {
    state.liveDeg = [deg1, deg2];
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
      updateAnimationTick(now);

      three.camTheta += (three.targetCamTheta - three.camTheta) * 0.14;
      three.camPhi += (three.targetCamPhi - three.camPhi) * 0.14;
      three.camRadius += (three.targetCamRadius - three.camRadius) * 0.14;
      updateCameraPosition();

      three.waypointGroups.forEach((grp, i) => {
        const pulse = 1 + Math.sin(now * 0.005 + i) * 0.08;
        grp.userData.ring.scale.set(pulse, pulse, 1);
      });

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
    state.phase = "idle";
    three.sparksActive = false;
    if (three.sparkPoints) three.sparkPoints.visible = false;
    updateTrail3D([]);

    const startDeg = customStartDeg || state.startDeg;
    const remainingWaypoints = state.waypoints.slice(fromWaypointIdx);

    if (fromWaypointIdx === 0) {
      state.completedWaypoints = 0;
      state.carryingPart = false;
      if (three.carriedPartMesh) three.carriedPartMesh.visible = false;
      if (three.floorPartMesh) {
        const pickWp = state.waypoints.find((w) => w.action === "pick");
        if (pickWp) {
          const p3 = to3D(pickWp.x, pickWp.y);
          three.floorPartMesh.position.set(p3.x, 0.22, p3.z);
          three.floorPartMesh.visible = true;
        }
      }
      updateWaypointVisuals(0);
    }

    try {
      const taskObj = state.meta.tasks.find((t) => t.id === state.activeTaskId);
      const resp = await fetch("/api/arm/solve-sequence", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          task_id: state.activeTaskId,
          task_name: taskObj ? taskObj.name : "Tarea en planta",
          algorithm: state.algorithm,
          start_deg: startDeg,
          waypoints: remainingWaypoints,
          obstacles: getActiveObstaclesList(),
          had_unexpected: state.unexpectedActive,
          use_memory: state.useMemory,
          record_run: true
        })
      });
      const json = await resp.json();
      if (json.status !== "success") return;

      state.lastResult = json.data;
      updateSummary(json.data, fromWaypointIdx);
      startStagePlayback(0, startDeg);
      refreshHistoryBadge();
    } catch (err) {
      el.verdictText.textContent = "Error al calcular el ciclo en Python.";
    }
  }

  function startStagePlayback(stageIndex, initialDeg = null) {
    const data = state.lastResult;
    if (!data || !data.stages || !data.stages[stageIndex]) return;

    state.paused = false;
    el.btnPlayPause.textContent = "Pausar";
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
    updateTrail3D(st.found ? st.path_frames : []);

    if (st.explored.length === 0) {
      state.phase = "failed";
      drawCspace(st, 0, -1, state.liveDeg);
      el.phaseBadge.textContent = `Detenido en ${st.label}`;
      el.phaseFill.style.width = "100%";
      return;
    }
    state.phase = "exploring";
  }

  function updateAnimationTick(now) {
    if (state.cspaceHover) return; // No pisar la vista previa cuando el usuario explora con el cursor

    const data = state.lastResult;
    if (!data || state.paused || state.phase === "idle" || state.phase === "done" || state.phase === "failed") {
      return;
    }

    const st = data.stages[state.stageIdx];
    if (!st) return;

    const dt = Math.min(0.05, (now - state.lastTickTime) / 1000);
    state.lastTickTime = now;
    const totalStages = data.stages.length;
    const stageBasePct = (state.stageIdx / totalStages) * 100;
    const stageSpanPct = 100 / totalStages;

    if (state.phase === "exploring") {
      const totalExp = st.explored.length;
      const rate = Math.max(24, totalExp / 2.3) * state.speed;
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
      el.phaseBadge.textContent = `Etapa ${state.stageIdx + 1}/${totalStages}: Probando (${Math.floor(state.expCursor)} / ${totalExp})`;

      if (state.expCursor >= totalExp) {
        setGhostAnglesDeg(0, 0, false);
        if (st.found && st.path_frames.length > 0) {
          state.phase = "moving";
          state.pathCursor = 0;
        } else {
          state.phase = "failed";
          el.phaseBadge.textContent = `Detenido en ${st.label}`;
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
      el.phaseBadge.textContent = `Etapa ${state.stageIdx + 1}/${totalStages}: ${st.label}`;

      if (state.pathCursor >= frames.length - 1) {
        // Accion practica al llegar al waypoint
        state.completedWaypoints += 1;
        updateWaypointVisuals(state.completedWaypoints);
        const t3 = to3D(st.target[0], st.target[1]);

        if (st.action === "pick") {
          state.carryingPart = true;
          if (three.floorPartMesh) three.floorPartMesh.visible = false;
          if (three.carriedPartMesh) three.carriedPartMesh.visible = true;
          triggerSparks(t3.x, t3.z, 0x38bdf8);
        } else if (st.action === "place") {
          state.carryingPart = false;
          if (three.carriedPartMesh) three.carriedPartMesh.visible = false;
          if (three.floorPartMesh) {
            three.floorPartMesh.position.set(t3.x, 0.22, t3.z);
            three.floorPartMesh.visible = true;
          }
          triggerSparks(t3.x, t3.z, 0x22c55e);
        } else {
          triggerSparks(t3.x, t3.z, 0xfbbf24);
        }

        if (state.stageIdx + 1 < totalStages) {
          startStagePlayback(state.stageIdx + 1, [curD1, curD2]);
        } else {
          state.phase = "done";
          el.phaseFill.style.width = "100%";
          el.phaseBadge.textContent = "¡Tarea completada!";
        }
      }
    }
  }

  function updateSummary(data, offsetWaypoints = 0) {
    const doneTotal = offsetWaypoints + data.completed_stages;
    const fullTotal = offsetWaypoints + data.total_stages;

    el.statExpanded.textContent = data.nodes_expanded.toLocaleString("es-MX");
    el.statEnergy.textContent = data.energy > 0 ? `${data.energy}` : "—";

    el.kpiStatusBox.classList.remove("is-ok", "is-warn", "is-fail");
    el.verdictBox.classList.remove("is-warn", "is-fail");

    if (!data.found) {
      el.statStatus.textContent = `Fallo (${doneTotal}/${fullTotal})`;
      el.kpiStatusBox.classList.add("is-fail");
      el.verdictBox.classList.add("is-fail");
      el.verdictText.textContent = data.reason || "El robot se detuvo porque no encontro camino libre.";
    } else if (data.is_optimal) {
      el.statStatus.textContent = `${fullTotal}/${fullTotal} · ${data.cycle_seconds} s`;
      el.kpiStatusBox.classList.add("is-ok");
      const memNote = data.from_cache ? " (Recuperado al instante desde Memoria SQL)" : "";
      el.verdictText.textContent =
        `Ciclo optimo completado en ${data.cycle_seconds} s con energia minima (${data.energy}) probando ${data.nodes_expanded} posturas.${memNote}`;
    } else {
      el.statStatus.textContent = `${fullTotal}/${fullTotal} · ${data.cycle_seconds} s`;
      el.kpiStatusBox.classList.add("is-warn");
      el.verdictBox.classList.add("is-warn");
      const memNote = data.from_cache ? " (Recuperado desde Memoria SQL)" : "";
      el.verdictText.textContent =
        `Completo la tarea, pero dio rodeos que elevaron la energia a ${data.energy} (ciclo de ${data.cycle_seconds} s).${memNote}`;
    }
  }

  // =========================================================================
  // MAPA DE POSTURAS + HOVER INTERACTIVO A 3D
  // =========================================================================
  const CSPACE_PAD = { l: 28, b: 24, t: 10, r: 10 };

  function drawCspace(stageData, expCount, activePathIdx, liveDeg = null) {
    if (!stageData) return;
    const dark = isDarkTheme();
    const N = state.meta.grid_n;
    const plotW = el.csCanvas.width - CSPACE_PAD.l - CSPACE_PAD.r;
    const plotH = el.csCanvas.height - CSPACE_PAD.t - CSPACE_PAD.b;
    const cw = plotW / N;
    const ch = plotH / N;
    const cspace = stageData.cspace;

    csCtx.fillStyle = dark ? "#161F28" : "#F7F8F4";
    csCtx.fillRect(0, 0, el.csCanvas.width, el.csCanvas.height);

    csCtx.fillStyle = dark ? "#1C2733" : "#FFFFFF";
    csCtx.fillRect(CSPACE_PAD.l, CSPACE_PAD.t, plotW, plotH);

    const toPxX = (i1) => CSPACE_PAD.l + i1 * cw;
    const toPxY = (i2) => CSPACE_PAD.t + (N - 1 - i2) * ch;

    for (let i1 = 0; i1 < N; i1++) {
      const row = cspace[i1];
      for (let i2 = 0; i2 < N; i2++) {
        const val = row[i2];
        if (val === 1) {
          csCtx.fillStyle = dark ? "#7C2D2D" : "#B94A4A";
          csCtx.fillRect(toPxX(i1), toPxY(i2), cw + 0.4, ch + 0.4);
        } else if (val === 2) {
          csCtx.fillStyle = "#22C55E";
          csCtx.fillRect(toPxX(i1), toPxY(i2), cw + 0.5, ch + 0.5);
        }
      }
    }

    const totalExp = Math.max(1, stageData.explored.length);
    for (let k = 0; k < expCount; k++) {
      const [e1, e2] = stageData.explored[k];
      if (cspace[e1][e2] === 2) continue;
      const ratio = k / totalExp;
      if (ratio < 0.45) csCtx.fillStyle = dark ? "rgba(56,142,130,0.52)" : "rgba(47,111,99,0.45)";
      else if (ratio < 0.85) csCtx.fillStyle = dark ? "rgba(79,184,168,0.68)" : "rgba(59,154,140,0.65)";
      else csCtx.fillStyle = dark ? "rgba(125,226,209,0.85)" : "rgba(38,166,154,0.82)";
      csCtx.fillRect(toPxX(e1), toPxY(e2), cw + 0.3, ch + 0.3);
    }

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

    csCtx.strokeStyle = dark ? "rgba(232,228,216,0.22)" : "rgba(30,42,51,0.22)";
    csCtx.lineWidth = 1;
    csCtx.strokeRect(CSPACE_PAD.l, CSPACE_PAD.t, plotW, plotH);

    csCtx.fillStyle = dark ? "#A9B0AC" : "#4B5A61";
    csCtx.font = "600 10px 'IBM Plex Sans', sans-serif";
    csCtx.textAlign = "center";
    csCtx.fillText("Giro del hombro (0° a 360°)", CSPACE_PAD.l + plotW / 2, el.csCanvas.height - 6);

    csCtx.save();
    csCtx.translate(11, CSPACE_PAD.t + plotH / 2);
    csCtx.rotate(-Math.PI / 2);
    csCtx.fillText("Giro del codo (0° a 360°)", 0, 0);
    csCtx.restore();
  }

  // =========================================================================
  // EVENTOS
  // =========================================================================
  function bindEvents() {
    el.algoPills.forEach((pill) => {
      pill.addEventListener("click", () => {
        state.algorithm = pill.dataset.algo;
        el.algoPills.forEach((p) => {
          const active = p === pill;
          p.classList.toggle("active", active);
          p.setAttribute("aria-selected", active ? "true" : "false");
        });
        runPythonSequence();
      });
    });

    el.btnEmergency.addEventListener("click", () => {
      state.unexpectedActive = !state.unexpectedActive;
      el.btnEmergency.classList.toggle("active", state.unexpectedActive);
      el.btnEmergency.textContent = state.unexpectedActive ? "Quitar imprevisto" : "Obstaculo imprevisto";
      rebuildThreeObstaclesAndWaypoints();

      // Si el robot iba a medio ciclo, recalcular desde su postura y etapa actual (Opcion C real)
      if (state.unexpectedActive && (state.phase === "exploring" || state.phase === "moving")) {
        runPythonSequence([...state.liveDeg], state.completedWaypoints);
      } else {
        runPythonSequence();
      }
    });

    el.btnPlayPause.addEventListener("click", () => {
      state.paused = !state.paused;
      el.btnPlayPause.textContent = state.paused ? "Reanudar" : "Pausar";
      if (!state.paused) state.lastTickTime = performance.now();
    });

    el.btnReplay.addEventListener("click", () => {
      runPythonSequence();
    });

    el.btnReset.addEventListener("click", () => {
      loadTask(state.activeTaskId, true);
    });

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

    el.btnCompare.addEventListener("click", openCompareModal);
    el.compareClose.addEventListener("click", () => el.compareModal.classList.remove("open"));
    el.compareModal.addEventListener("click", (e) => {
      if (e.target === el.compareModal) el.compareModal.classList.remove("open");
    });

    // Modal Bitacora SQL + Mini-RAG + Memoria
    el.btnHistory.addEventListener("click", openLogModal);
    el.logClose.addEventListener("click", () => el.logModal.classList.remove("open"));
    el.logModal.addEventListener("click", (e) => {
      if (e.target === el.logModal) el.logModal.classList.remove("open");
    });
    el.logTabs.forEach((tab) => {
      tab.addEventListener("click", () => switchLogTab(tab.dataset.armTab));
    });
    el.ragChips.forEach((chip) => {
      chip.addEventListener("click", () => {
        el.ragInput.value = chip.dataset.ragQ;
        runRagQuery(chip.dataset.ragQ);
      });
    });
    el.ragForm.addEventListener("submit", (e) => {
      e.preventDefault();
      runRagQuery(el.ragInput.value);
    });
    el.sqlFilters.forEach((btn) => {
      btn.addEventListener("click", () => {
        state.sqlFilter = btn.dataset.sqlFilter;
        el.sqlFilters.forEach((b) => b.classList.toggle("active", b === btn));
        loadHistoryData();
      });
    });
    el.btnClearRuns.addEventListener("click", () => clearStorage("runs"));
    el.btnClearCache.addEventListener("click", () => clearStorage("cache"));
    el.toggleMemory.addEventListener("change", () => {
      state.useMemory = el.toggleMemory.checked;
    });

    // Hover en el mapa C-Space -> mueve el brazo fantasma 3D al instante
    el.csCanvas.addEventListener("pointermove", (e) => {
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
      el.hoverHud.textContent = val === 1
        ? `Postura (${d1}°, ${d2}°) — ¡Choca con una maquina!`
        : val === 2
          ? `Postura (${d1}°, ${d2}°) — Alcanza el punto objetivo`
          : `Postura (${d1}°, ${d2}°) — Movimiento libre`;
      el.hoverHud.hidden = false;
    });

    el.csCanvas.addEventListener("pointerleave", () => {
      state.cspaceHover = null;
      setGhostAnglesDeg(0, 0, false);
      el.hoverHud.hidden = true;
      state.lastTickTime = performance.now();
    });

    // Interaccion 3D (arrastrar obstaculos/waypoints o girar camara)
    const domEl = three.renderer ? three.renderer.domElement : null;
    if (!domEl) return;

    const getNdc = (evt) => {
      const rect = domEl.getBoundingClientRect();
      return new window.THREE.Vector2(
        ((evt.clientX - rect.left) / rect.width) * 2 - 1,
        -((evt.clientY - rect.top) / rect.height) * 2 + 1
      );
    };

    const getInteractiveMeshes = () => {
      const list = [];
      three.obstacleGroups.forEach((g) => list.push(...g.children));
      three.waypointGroups.forEach((g) => list.push(...g.children));
      return list;
    };

    domEl.addEventListener("pointerdown", (e) => {
      three.raycaster.setFromCamera(getNdc(e), three.camera);
      const hits = three.raycaster.intersectObjects(getInteractiveMeshes(), false);
      const floorHit = new window.THREE.Vector3();
      three.raycaster.ray.intersectPlane(three.floorPlane, floorHit);

      if (hits.length > 0) {
        const meta = hits[0].object.userData;
        const grp = meta.parentGroup;
        three.dragTarget = {
          type: meta.dragType,
          index: meta.index,
          offsetX: grp.position.x - floorHit.x,
          offsetZ: grp.position.z - floorHit.z
        };
        domEl.style.cursor = "grabbing";
      } else {
        three.dragTarget = { type: "orbit", lastX: e.clientX, lastY: e.clientY };
        domEl.style.cursor = "move";
      }
      domEl.setPointerCapture(e.pointerId);
    });

    domEl.addEventListener("pointermove", (e) => {
      if (!three.dragTarget) {
        three.raycaster.setFromCamera(getNdc(e), three.camera);
        const hits = three.raycaster.intersectObjects(getInteractiveMeshes(), false);
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

      three.raycaster.setFromCamera(getNdc(e), three.camera);
      const floorHit = new window.THREE.Vector3();
      if (!three.raycaster.ray.intersectPlane(three.floorPlane, floorHit)) return;

      const nx = floorHit.x + three.dragTarget.offsetX;
      const nz = floorHit.z + three.dragTarget.offsetZ;
      const p2d = to2D(nx, nz);

      if (three.dragTarget.type === "waypoint") {
        const wp = state.waypoints[three.dragTarget.index];
        wp.x = Math.max(25, Math.min(415, p2d.x));
        wp.y = Math.max(25, Math.min(355, p2d.y));
        const clamped3 = to3D(wp.x, wp.y);
        three.waypointGroups[three.dragTarget.index].position.set(clamped3.x, 0.02, clamped3.z);
        if (wp.action === "pick" && three.floorPartMesh && !state.carryingPart) {
          three.floorPartMesh.position.set(clamped3.x, 0.22, clamped3.z);
        }
      } else if (three.dragTarget.type === "obstacle") {
        const idx = three.dragTarget.index;
        const ob = idx < state.obstacles.length ? state.obstacles[idx] : state.unexpectedSpec;
        if (ob) {
          ob.x = Math.max(10, Math.min(430 - ob.w, p2d.x - ob.w / 2));
          ob.y = Math.max(10, Math.min(370 - ob.h, p2d.y - ob.h / 2));
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

    const themeBtn = document.getElementById("btnThemeToggle");
    if (themeBtn) {
      themeBtn.addEventListener("click", () => {
        setTimeout(() => {
          updateSceneTheme();
          if (state.lastResult && state.lastResult.stages[state.stageIdx]) {
            drawCspace(state.lastResult.stages[state.stageIdx], Math.floor(state.expCursor), -1, state.liveDeg);
          }
        }, 40);
      });
    }
  }

  async function openCompareModal() {
    el.compareModal.classList.add("open");
    el.compareCards.innerHTML = `<p class="sv-pane-intro">Ejecutando la tarea completa con las 5 estrategias en Python...</p>`;

    try {
      const resp = await fetch("/api/arm/compare-sequence", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          start_deg: state.startDeg,
          waypoints: state.waypoints,
          obstacles: getActiveObstaclesList()
        })
      });
      const json = await resp.json();
      if (json.status !== "success") return;

      const rows = json.data.comparisons;
      const maxExp = Math.max(...rows.map((r) => r.nodes_expanded), 1);
      const maxEn = Math.max(...rows.map((r) => r.energy || 0), 1);

      el.compareCards.innerHTML = rows.map((row) => {
        const expPct = Math.round((row.nodes_expanded / maxExp) * 100);
        const enPct = row.found ? Math.round((row.energy / maxEn) * 100) : 100;

        let cardCls = "";
        let badgeHtml = `<span class="arm-cmp-badge fail">Fallo (${row.completed_stages}/${row.total_stages})</span>`;
        if (row.found && row.is_optimal) {
          cardCls = row.algorithm_id === "astar" ? "is-winner" : "";
          badgeHtml = `<span class="arm-cmp-badge ok">Optima · ${row.cycle_seconds} s</span>`;
        } else if (row.found) {
          badgeHtml = `<span class="arm-cmp-badge warn">Rodeo · ${row.cycle_seconds} s</span>`;
        } else {
          cardCls = "is-failed";
        }

        return `
          <div class="arm-cmp-card ${cardCls}">
            <div class="arm-cmp-top">
              <span class="arm-cmp-name">${escapeHtml(row.algorithm_name)}</span>
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
          </div>
        `;
      }).join("");

      const astar = rows.find((r) => r.algorithm_id === "astar");
      const ucs = rows.find((r) => r.algorithm_id === "ucs");
      const failed = rows.filter((r) => !r.found).map((r) => r.algorithm_name);
      if (astar && ucs && astar.found) {
        const failText = failed.length ? ` En contraste, ${failed.join(", ")} no logro completar el lote.` : "";
        el.compareSummary.textContent =
          `Resumen de produccion: A* completo la tarea en ${astar.cycle_seconds} s con energia minima (${astar.energy}) ` +
          `probando ${astar.nodes_expanded} posturas, frente a ${ucs.nodes_expanded} de Costo Uniforme.${failText}`;
      } else {
        el.compareSummary.textContent = "Con los obstaculos actuales no es posible completar la secuencia.";
      }
    } catch (err) {
      el.compareCards.innerHTML = `<p class="sv-pane-intro">Error al comparar estrategias en Python.</p>`;
    }
  }

  // =========================================================================
  // BITACORA SQL, MEMORIA DE RUTAS (CBR) Y MINI-RAG LOCAL
  // =========================================================================
  async function refreshHistoryBadge() {
    try {
      const resp = await fetch("/api/arm/history?limit=1");
      const json = await resp.json();
      if (json.status === "success" && el.historyCount) {
        el.historyCount.textContent = String(json.data.kpis.total_runs || 0);
      }
    } catch (err) {
      // Silencioso si aun no esta disponible
    }
  }

  function switchLogTab(tabName) {
    el.logTabs.forEach((t) => {
      const active = t.dataset.armTab === tabName;
      t.classList.toggle("active", active);
      t.setAttribute("aria-selected", active ? "true" : "false");
    });
    el.logPanes.forEach((p) => {
      const active = p.dataset.armPane === tabName;
      p.classList.toggle("active", active);
      p.hidden = !active;
    });
    if (tabName === "history" || tabName === "memory") {
      loadHistoryData();
    }
  }

  async function openLogModal() {
    el.logModal.classList.add("open");
    await loadHistoryData();
  }

  async function loadHistoryData() {
    try {
      const resp = await fetch(`/api/arm/history?filter=${encodeURIComponent(state.sqlFilter)}&limit=40`);
      const json = await resp.json();
      if (json.status !== "success") return;

      const { kpis, runs, cache_entries: cacheEntries } = json.data;
      if (el.historyCount) el.historyCount.textContent = String(kpis.total_runs);
      el.sqlTotal.textContent = String(kpis.total_runs);
      el.sqlFailures.textContent = String(kpis.total_failures);
      el.sqlCached.textContent = String(kpis.total_from_cache);
      el.sqlSavings.textContent = kpis.astar_energy_savings_pct !== null ? `${kpis.astar_energy_savings_pct}%` : "—";

      renderRunsList(runs);
      renderCacheList(cacheEntries);
    } catch (err) {
      el.runsList.innerHTML = `<p class="sv-pane-intro">No se pudo cargar la bitacora SQL.</p>`;
    }
  }

  function renderRunsList(runs) {
    if (!runs || !runs.length) {
      el.runsList.innerHTML = `<p class="sv-pane-intro">No hay registros para este filtro todavia.</p>`;
      return;
    }

    el.runsList.innerHTML = runs.map((r) => {
      const tagCls = !r.found ? "is-fail" : r.is_optimal ? "is-ok" : "is-warn";
      const tagText = !r.found
        ? `Fallo (${r.completed_stages}/${r.total_stages})`
        : r.is_optimal
          ? `Optima · ${r.cycle_seconds} s`
          : `Rodeo · ${r.cycle_seconds} s`;
      const memTag = r.from_cache ? `<span class="arm-run-tag is-ok">Memoria SQL</span>` : "";
      const unexpTag = r.had_unexpected ? `<span class="arm-run-tag is-warn">Imprevisto</span>` : "";

      return `
        <div class="arm-run-card">
          <div class="arm-run-main">
            <div class="arm-run-title">
              <span>#${r.id} · ${escapeHtml(r.task_name)}</span>
              <span class="arm-run-tag ${tagCls}">${tagText}</span>
              ${memTag}
              ${unexpTag}
            </div>
            <div class="arm-run-meta">
              <strong>${escapeHtml(r.algorithm_name)}</strong> · ${r.nodes_expanded} posturas · Energia ${r.energy}
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
    state.startDeg = [...(sc.start_deg || [170, 15])];
    state.waypoints = sc.waypoints.map((w) => ({ ...w }));
    state.unexpectedActive = Boolean(sc.had_unexpected);
    const allObs = (sc.obstacles || []).map((o) => ({ ...o }));
    state.obstacles = allObs.filter((o) => o.id !== "obs_emergency");
    const emerg = allObs.find((o) => o.id === "obs_emergency");
    if (emerg) state.unexpectedSpec = emerg;

    el.presetButtons.querySelectorAll(".arm-preset-btn").forEach((b) => {
      b.classList.toggle("active", b.dataset.task === state.activeTaskId);
    });
    el.algoPills.forEach((p) => {
      const active = p.dataset.algo === state.algorithm;
      p.classList.toggle("active", active);
      p.setAttribute("aria-selected", active ? "true" : "false");
    });
    el.btnEmergency.classList.toggle("active", state.unexpectedActive);
    el.btnEmergency.textContent = state.unexpectedActive ? "Quitar imprevisto" : "Obstaculo imprevisto";

    el.logModal.classList.remove("open");
    rebuildThreeObstaclesAndWaypoints();
    runPythonSequence();
  }

  async function runRagQuery(question) {
    const q = String(question || "").trim();
    if (!q) return;
    el.ragAnswer.textContent = "Consultando registros en SQLite...";

    try {
      const resp = await fetch("/api/arm/rag", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q })
      });
      const json = await resp.json();
      if (json.status !== "success") return;

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
      el.ragAnswer.textContent = "Error al consultar el Mini-RAG en Python.";
    }
  }

  async function clearStorage(scope) {
    try {
      await fetch(`/api/arm/history?scope=${encodeURIComponent(scope)}`, { method: "DELETE" });
      await loadHistoryData();
    } catch (err) {
      // Silencioso
    }
  }

  init();
});
