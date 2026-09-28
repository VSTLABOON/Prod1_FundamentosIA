/**
 * app.js
 * Logica interactiva del Compendio de Inteligencia Artificial.
 * 
 * Modulos implementados:
 * 1. Navegacion entre secciones principales (Antecedentes, Clasificacion, Glosario).
 * 2. Buscador global sincronizado con el Glosario de conceptos.
 * 3. Boton de concepto aleatorio integrado en la barra de herramientas.
 * 4. Visor Lightbox para ampliacion de infografias en alta definicion.
 * 5. Perspectiva 3D (3D Tilt) con iluminacion dinamica en tarjetas de conceptos.
 * 6. Ventana modal de ficha tecnica profunda con pestanas navegables.
 * 7. Alternador de tema claro / oscuro persistente en localStorage.
 * 
 * Sin uso de emojis ni elementos visuales distractores.
 */

document.addEventListener("DOMContentLoaded", () => {
  // Estado general de la aplicacion
  const state = {
    currentSection: "sectionAntecedentes",
    concepts: [],
    searchQuery: ""
  };

  // Referencias a elementos del DOM
  const dom = {
    // Navegacion principal
    navLinks: document.querySelectorAll(".nav-link-btn"),
    sections: document.querySelectorAll(".main-page-section"),
    globalSearchInput: document.getElementById("globalSearchInput"),
    themeToggleBtn: document.getElementById("btnThemeToggle"),
    shuffleBtn: document.getElementById("btnShuffle"),
    // Lightbox
    lightboxModal: document.getElementById("lightboxModal"),
    lightboxImage: document.getElementById("lightboxImage"),
    lightboxCloseBtn: document.getElementById("lightboxCloseBtn"),
    // Glosario
    gridContainer: document.getElementById("conceptsGrid"),
    // Modal Concepto
    modalBackdrop: document.getElementById("conceptModal"),
    modalCloseBtn: document.getElementById("modalCloseBtn"),
    modalTitle: document.getElementById("modalTitle"),
    modalTitleEn: document.getElementById("modalTitleEn"),
    modalCategory: document.getElementById("modalCategory"),
    modalDifficulty: document.getElementById("modalDifficulty"),
    modalHeroImage: document.getElementById("modalHeroImage"),
    modalPlaceholder: document.getElementById("modalPlaceholder"),
    modalTabItems: document.querySelectorAll(".modal-tab-item"),
    modalTabContent: document.getElementById("modalTabContent")
  };

  let activeModalConcept = null;

  /* ==========================================================================
     1. GESTION DE TEMA (MODO CLARO / OSCURO)
     ========================================================================== */
  function initTheme() {
    const savedTheme = localStorage.getItem("ai_glossary_theme");
    if (savedTheme) {
      document.documentElement.setAttribute("data-theme", savedTheme);
    } else if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
      document.documentElement.setAttribute("data-theme", "dark");
    } else {
      document.documentElement.setAttribute("data-theme", "light");
    }

    if (dom.themeToggleBtn) {
      dom.themeToggleBtn.addEventListener("click", () => {
        const current = document.documentElement.getAttribute("data-theme");
        const next = current === "dark" ? "light" : "dark";
        document.documentElement.setAttribute("data-theme", next);
        localStorage.setItem("ai_glossary_theme", next);
      });
    }
  }

  /* ==========================================================================
     2. CONTROLADOR DE NAVEGACION POR SECCIONES
     ========================================================================== */
  function switchSection(targetSectionId) {
    state.currentSection = targetSectionId;

    // Actualizar botones de navegacion
    dom.navLinks.forEach(link => {
      const isTarget = link.getAttribute("data-target") === targetSectionId;
      link.classList.toggle("active", isTarget);
    });

    // Actualizar visibilidad de secciones
    dom.sections.forEach(sec => {
      const isTarget = sec.id === targetSectionId;
      sec.classList.toggle("active", isTarget);
    });

    // Sincronizar hash de la URL
    const hashMap = {
      sectionAntecedentes: "antecedentes",
      sectionClasificacion: "clasificacion",
      sectionMachineLearning: "machine-learning",
      sectionGlosario: "glosario",
      sectionEnsayo: "ensayo"
    };
    if (hashMap[targetSectionId]) {
      history.replaceState(null, "", `#${hashMap[targetSectionId]}`);
    }

    if (targetSectionId === "sectionGlosario") {
      renderGrid();
    }
  }

  function initNavigation() {
    dom.navLinks.forEach(btn => {
      btn.addEventListener("click", () => {
        const target = btn.getAttribute("data-target");
        switchSection(target);
      });
    });

    const hash = window.location.hash.toLowerCase();
    if (hash === "#clasificacion") {
      switchSection("sectionClasificacion");
    } else if (hash === "#machine-learning" || hash === "#ml") {
      switchSection("sectionMachineLearning");
    } else if (hash === "#glosario") {
      switchSection("sectionGlosario");
    } else if (hash === "#ensayo") {
      switchSection("sectionEnsayo");
    } else {
      switchSection("sectionAntecedentes");
    }
  }

  /* ==========================================================================
     3. BUSCADOR GLOBAL INTELIGENTE
     ========================================================================== */
  let searchDebounce = null;

  function handleSearchInput(query) {
    state.searchQuery = query.trim();

    // Al tipear, si no estamos en el Glosario, cambiar inmediatamente a el
    if (state.currentSection !== "sectionGlosario" && state.searchQuery.length > 0) {
      switchSection("sectionGlosario");
    }

    clearTimeout(searchDebounce);
    searchDebounce = setTimeout(() => {
      loadConcepts();
    }, 200);
  }

  if (dom.globalSearchInput) {
    dom.globalSearchInput.addEventListener("input", (e) => {
      handleSearchInput(e.target.value);
    });
  }

  /* ==========================================================================
     4. MODAL LIGHTBOX PARA AMPLIAR INFOGRAFIAS EN ALTA RESOLUCION
     ========================================================================== */
  function openLightbox(imageSrc, imageAlt) {
    if (!dom.lightboxModal || !dom.lightboxImage) return;
    dom.lightboxImage.src = imageSrc;
    dom.lightboxImage.alt = imageAlt || "Infografia ampliada";
    dom.lightboxModal.classList.add("open");
    document.body.style.overflow = "hidden";
  }

  function closeLightbox() {
    if (!dom.lightboxModal) return;
    dom.lightboxModal.classList.remove("open");
    document.body.style.overflow = "";
    if (dom.lightboxImage) dom.lightboxImage.src = "";
  }

  function initLightbox() {
    document.querySelectorAll(".zoomable-trigger, .btn-expand-lightbox").forEach(elem => {
      elem.addEventListener("click", (e) => {
        e.stopPropagation();
        const imgUrl = elem.getAttribute("data-img");
        const altText = elem.getAttribute("data-alt");
        if (imgUrl) {
          openLightbox(imgUrl, altText);
        }
      });
    });

    if (dom.lightboxCloseBtn) {
      dom.lightboxCloseBtn.addEventListener("click", closeLightbox);
    }

    if (dom.lightboxModal) {
      dom.lightboxModal.addEventListener("click", (e) => {
        if (e.target === dom.lightboxModal || e.target.classList.contains("lightbox-scroll-area")) {
          closeLightbox();
        }
      });
    }

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && dom.lightboxModal && dom.lightboxModal.classList.contains("open")) {
        closeLightbox();
      }
    });
  }

  /* ==========================================================================
     5. CARGA Y CONSULTA DE CONCEPTOS DEL GLOSARIO (API REST)
     ========================================================================== */
  async function loadConcepts() {
    try {
      const params = new URLSearchParams();
      if (state.searchQuery) {
        params.append("search", state.searchQuery);
      }

      const response = await fetch(`/api/concepts?${params.toString()}`);
      const result = await response.json();

      if (result.status === "success") {
        state.concepts = result.data;
        renderGrid();
      }
    } catch (error) {
      console.error("[API ERROR] No se pudieron cargar los conceptos:", error);
    }
  }

  /* ==========================================================================
     6. RENDERIZADO DIRECTO DE LA CUADRICULA Y PERSPECTIVA 3D TILT
     ========================================================================== */
  function renderGrid() {
    if (!dom.gridContainer) return;

    if (state.concepts.length === 0) {
      dom.gridContainer.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 48px 20px; color: var(--ink-soft);">
          <p style="font-size: 1.25rem; font-family: 'Fraunces', serif; margin-bottom: 6px;">No se encontraron conceptos</p>
          <p style="font-size: 0.92rem;">Prueba modificando los criterios de busqueda.</p>
        </div>
      `;
      return;
    }

    dom.gridContainer.innerHTML = state.concepts.map(concept => {
      const isFav = concept.is_favorite === 1;
      const mediaHtml = concept.has_custom_image
        ? `<img class="card-image" src="${concept.image_url}" alt="${concept.title}" loading="lazy" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';" />
           <div class="card-placeholder-fallback" style="display:none;">
             <div class="placeholder-icon-wrap">
               <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
             </div>
             <span class="placeholder-label">${concept.category}</span>
           </div>`
        : `<div class="card-placeholder-fallback">
             <div class="placeholder-icon-wrap">
               <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="10"></circle><path d="M12 16v-4M12 8h.01"></path></svg>
             </div>
             <span class="placeholder-label">${concept.category}</span>
           </div>`;

      const tagsHtml = concept.tags
        ? concept.tags.split(",").slice(0, 3).map(t => `<span class="tag-label">${t.trim()}</span>`).join("")
        : "";

      return `
        <article class="concept-card" data-id="${concept.id}" tabindex="0">
          <div class="card-glare"></div>
          <div class="card-media-wrapper">
            ${mediaHtml}
            <div class="card-floating-meta">
              <span class="category-badge">${concept.category}</span>
              <button class="btn-card-favorite ${isFav ? 'favorited' : ''}" data-id="${concept.id}" title="Marcar como favorito" aria-label="Favorito">
                <svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>
              </button>
            </div>
          </div>
          <div class="card-content">
            <div class="card-header-line">
              <h3 class="card-title">${concept.title}</h3>
              <span class="difficulty-pill ${concept.difficulty}">${concept.difficulty}</span>
            </div>
            <div class="card-title-en">${concept.title_en}</div>
            <p class="card-summary">${concept.short_desc}</p>
            <div class="card-footer">
              <div class="card-tags">${tagsHtml}</div>
              <span class="card-action-link">
                Ficha tecnica
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
              </span>
            </div>
          </div>
        </article>
      `;
    }).join("");

    attachCardInteractions();
  }

  function attachCardInteractions() {
    const cards = document.querySelectorAll(".concept-card");

    cards.forEach(card => {
      card.addEventListener("mousemove", (e) => {
        const rect = card.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;

        const rotateX = ((mouseY / rect.height) - 0.5) * -14;
        const rotateY = ((mouseX / rect.width) - 0.5) * 14;

        card.style.transform = `perspective(1000px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg) translateY(-4px)`;

        const glareX = (mouseX / rect.width) * 100;
        const glareY = (mouseY / rect.height) * 100;
        card.style.setProperty("--glare-x", `${glareX}%`);
        card.style.setProperty("--glare-y", `${glareY}%`);
      });

      card.addEventListener("mouseleave", () => {
        card.style.transform = "perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0px)";
      });

      card.addEventListener("click", (e) => {
        if (e.target.closest(".btn-card-favorite")) return;
        const conceptId = parseInt(card.getAttribute("data-id"), 10);
        openModalForConcept(conceptId);
      });

      card.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          const conceptId = parseInt(card.getAttribute("data-id"), 10);
          openModalForConcept(conceptId);
        }
      });
    });

    document.querySelectorAll(".btn-card-favorite").forEach(btn => {
      btn.addEventListener("click", async (e) => {
        e.stopPropagation();
        const conceptId = parseInt(btn.getAttribute("data-id"), 10);
        await toggleFavoriteState(conceptId, btn);
      });
    });
  }

  async function toggleFavoriteState(conceptId, buttonElement) {
    try {
      const response = await fetch(`/api/concepts/${conceptId}/favorite`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      });
      const result = await response.json();
      if (result.status === "success") {
        const isFav = result.is_favorite;
        buttonElement.classList.toggle("favorited", isFav);

        const item = state.concepts.find(c => c.id === conceptId);
        if (item) item.is_favorite = isFav ? 1 : 0;
      }
    } catch (error) {
      console.error("[FAVORITE ERROR] No se pudo cambiar el estado:", error);
    }
  }

  /* ==========================================================================
     7. VENTANA MODAL (FICHA TECNICA PROFUNDA DEL CONCEPTO)
     ========================================================================== */
  function openModalForConcept(conceptId) {
    const concept = state.concepts.find(c => c.id === conceptId);
    if (!concept) return;

    activeModalConcept = concept;

    dom.modalTitle.textContent = concept.title;
    dom.modalTitleEn.textContent = concept.title_en;
    dom.modalCategory.textContent = concept.category;
    dom.modalDifficulty.textContent = concept.difficulty;
    dom.modalDifficulty.className = `difficulty-pill ${concept.difficulty}`;

    if (concept.has_custom_image) {
      dom.modalHeroImage.src = concept.image_url;
      dom.modalHeroImage.style.display = "block";
      dom.modalPlaceholder.style.display = "none";
    } else {
      dom.modalHeroImage.style.display = "none";
      dom.modalPlaceholder.style.display = "flex";
      dom.modalPlaceholder.querySelector(".placeholder-label").textContent = concept.category;
    }

    setActiveModalTab("definition");
    dom.modalBackdrop.classList.add("open");
    document.body.style.overflow = "hidden";
  }

  function closeModal() {
    dom.modalBackdrop.classList.remove("open");
    document.body.style.overflow = "";
    activeModalConcept = null;
  }

  function setActiveModalTab(tabKey) {
    if (!activeModalConcept) return;

    dom.modalTabItems.forEach(item => {
      item.classList.toggle("active", item.getAttribute("data-tab") === tabKey);
    });

    let contentHtml = "";
    switch (tabKey) {
      case "definition":
        contentHtml = `
          <p style="font-size: 1.05rem; line-height: 1.7; margin-bottom: 14px;">
            ${activeModalConcept.full_definition}
          </p>
          <div style="margin-top: 16px; padding: 12px 16px; background: var(--bg-raised); border-radius: var(--radius-md); border-left: 3px solid var(--teal);">
            <strong style="color: var(--teal); display: block; margin-bottom: 4px; font-size: 0.82rem; text-transform: uppercase;">Resumen Ejecutivo</strong>
            <p style="margin: 0; font-size: 0.9rem; color: var(--ink-soft);">${activeModalConcept.short_desc}</p>
          </div>
        `;
        break;
      case "example":
        contentHtml = `
          <h4 style="font-size: 1.05rem; color: var(--gold); margin-bottom: 8px;">Aplicacion en el Mundo Real</h4>
          <p style="font-size: 0.98rem; line-height: 1.65; margin-bottom: 14px;">
            ${activeModalConcept.real_world_example}
          </p>
        `;
        break;
      case "technical":
        contentHtml = `
          <h4 style="font-size: 1.05rem; color: var(--ink); margin-bottom: 8px;">Formulacion y Mecanismo Tecnico</h4>
          <div class="technical-box">
            <code>${activeModalConcept.technical_detail}</code>
          </div>
        `;
        break;
      case "history":
        contentHtml = `
          <h4 style="font-size: 1.05rem; color: var(--ink); margin-bottom: 8px;">Hito Historico y Contexto</h4>
          <p style="font-size: 0.98rem; line-height: 1.65;">
            ${activeModalConcept.historical_milestone}
          </p>
        `;
        break;
    }

    dom.modalTabContent.innerHTML = contentHtml;
  }

  dom.modalTabItems.forEach(item => {
    item.addEventListener("click", () => {
      setActiveModalTab(item.getAttribute("data-tab"));
    });
  });

  if (dom.modalCloseBtn) dom.modalCloseBtn.addEventListener("click", closeModal);
  if (dom.modalBackdrop) {
    dom.modalBackdrop.addEventListener("click", (e) => {
      if (e.target === dom.modalBackdrop) closeModal();
    });
  }

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && dom.modalBackdrop.classList.contains("open")) {
      closeModal();
    }
  });

  /* ==========================================================================
     8. BOTON CONCEPTO ALEATORIO
     ========================================================================== */
  if (dom.shuffleBtn) {
    dom.shuffleBtn.addEventListener("click", () => {
      if (state.concepts.length === 0) return;
      const randomIndex = Math.floor(Math.random() * state.concepts.length);
      openModalForConcept(state.concepts[randomIndex].id);
    });
  }

  /* ==========================================================================
     9. SIMULADOR INTERACTIVO DE MACHINE LEARNING (INFERENCIA EN TIEMPO REAL)
     ========================================================================== */
  function initMachineLearningSimulator() {
    const elMonto = document.getElementById("simMonto");
    const elDistancia = document.getElementById("simDistancia");
    const elHora = document.getElementById("simHora");
    const elDispositivo = document.getElementById("simDispositivo");

    const valMonto = document.getElementById("simMontoValue");
    const valDistancia = document.getElementById("simDistanciaValue");
    const valHora = document.getElementById("simHoraValue");
    const valDispositivo = document.getElementById("simDispositivoValue");

    const elMathLogit = document.getElementById("simMathLogit");
    const elRiskText = document.getElementById("simRiskScoreText");
    const elRiskBar = document.getElementById("simRiskBar");
    const elVerdictCard = document.getElementById("simVerdictCard");
    const elVerdictTitle = document.getElementById("simVerdictTitle");
    const elVerdictText = document.getElementById("simVerdictText");

    if (!elMonto || !elDistancia || !elHora || !elDispositivo) return;

    function runInference() {
      const monto = parseFloat(elMonto.value) || 0;
      const distancia = parseFloat(elDistancia.value) || 0;
      const hora = parseInt(elHora.value, 10) || 0;
      const dispositivoNuevo = parseInt(elDispositivo.value, 10) === 1 ? 1 : 0;

      // Actualizar etiquetas de valores de entrada
      if (valMonto) valMonto.textContent = `$${monto.toLocaleString()} USD`;
      if (valDistancia) valDistancia.textContent = `${distancia.toLocaleString()} km`;

      let horaStr = `${hora.toString().padStart(2, "0")}:00 hrs`;
      const esMadrugada = hora >= 2 && hora <= 5;
      if (esMadrugada) {
        horaStr += " (Madrugada atipica)";
      } else if (hora >= 6 && hora <= 12) {
        horaStr += " (Manana)";
      } else if (hora >= 13 && hora <= 19) {
        horaStr += " (Tarde)";
      } else {
        horaStr += " (Noche)";
      }
      if (valHora) valHora.textContent = horaStr;
      if (valDispositivo) valDispositivo.textContent = dispositivoNuevo === 1 ? "Nuevo / Desconocido" : "Habitual del Cliente";

      // Parametros matematicos del modelo de Regresion Logistica entrenado
      const bias = -3.50;
      const wMonto = 0.00085;
      const wDistancia = 0.0022;
      const wHora = esMadrugada ? 1.35 : 0;
      const wDispositivo = dispositivoNuevo ? 1.65 : 0;

      // Calculo del Logit z
      const z = bias + (wMonto * monto) + (wDistancia * distancia) + wHora + wDispositivo;

      // Calculo de la funcion logistica (Sigmoide): P = 1 / (1 + e^(-z))
      const probability = 1 / (1 + Math.exp(-z));
      const percentage = probability * 100;

      // Actualizar representaciones matematicas en el DOM
      if (elMathLogit) {
        const signStr = z >= 0 ? `+${z.toFixed(2)}` : z.toFixed(2);
        elMathLogit.textContent = signStr;
      }
      if (elRiskText) {
        elRiskText.textContent = `${percentage.toFixed(1)}%`;
      }
      if (elRiskBar) {
        elRiskBar.style.width = `${Math.min(100, Math.max(3, percentage))}%`;
      }

      // Actualizar clases de alerta
      [elRiskText, elRiskBar, elVerdictCard].forEach(elem => {
        if (elem) elem.classList.remove("safe", "warning", "danger");
      });

      // Evaluacion del veredicto frente al umbral
      if (percentage < 30) {
        if (elRiskText) elRiskText.classList.add("safe");
        if (elRiskBar) elRiskBar.classList.add("safe");
        if (elVerdictCard) elVerdictCard.classList.add("safe");
        if (elVerdictTitle) elVerdictTitle.textContent = "TRANSACCION AUTORIZADA";
        if (elVerdictText) {
          elVerdictText.textContent = `El score de riesgo estimado (${percentage.toFixed(1)}%) es bajo y se mantiene dentro de los parametros normales. El modelo no detecta anomalias criticas en el patron transaccional.`;
        }
      } else if (percentage < 50) {
        if (elRiskText) elRiskText.classList.add("warning");
        if (elRiskBar) elRiskBar.classList.add("warning");
        if (elVerdictCard) elVerdictCard.classList.add("warning");
        if (elVerdictTitle) elVerdictTitle.textContent = "AUTORIZADA CON ALERTA PREVENTIVA";
        if (elVerdictText) {
          elVerdictText.textContent = `El score de riesgo estimado (${percentage.toFixed(1)}%) refleja sospecha moderada cercana al umbral de corte. Se autoriza la transaccion pero se despacha una solicitud de verificacion al dispositivo del usuario.`;
        }
      } else {
        if (elRiskText) elRiskText.classList.add("danger");
        if (elRiskBar) elRiskBar.classList.add("danger");
        if (elVerdictCard) elVerdictCard.classList.add("danger");
        if (elVerdictTitle) elVerdictTitle.textContent = "TRANSACCION BLOQUEADA (FRAUDE DETECTADO)";
        if (elVerdictText) {
          elVerdictText.textContent = `El score de riesgo estimado (${percentage.toFixed(1)}%) supera el umbral de decision del 50%. La conjuncion atipica de parametros dispara el protocolo de proteccion bancaria y deniega la operacion.`;
        }
      }
    }

    // Escuchar eventos en tiempo real
    [elMonto, elDistancia, elHora].forEach(input => {
      input.addEventListener("input", runInference);
    });
    elDispositivo.addEventListener("change", runInference);

    // Computo inicial
    runInference();
  }

  /* ==========================================================================
     10. INDICE INTERACTIVO DEL ENSAYO ACADEMICO
     ========================================================================== */
  function initEssayToc() {
    const tocLinks = document.querySelectorAll(".toc-nav-link");
    const chapters = document.querySelectorAll(".essay-chapter");

    tocLinks.forEach(link => {
      link.addEventListener("click", (e) => {
        const href = link.getAttribute("href");
        if (href && href.startsWith("#")) {
          e.preventDefault();
          const targetElem = document.querySelector(href);
          if (targetElem) {
            targetElem.scrollIntoView({ behavior: "smooth", block: "start" });
            history.replaceState(null, "", href);
          }
        }
      });
    });

    // Observer para resaltar la seccion activa en el indice durante el scroll
    if ("IntersectionObserver" in window && chapters.length > 0) {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const id = entry.target.id;
            tocLinks.forEach(l => {
              const matches = l.getAttribute("href") === `#${id}`;
              l.classList.toggle("active", matches);
            });
          }
        });
      }, {
        rootMargin: "-15% 0px -70% 0px"
      });

      chapters.forEach(ch => observer.observe(ch));
    }
  }

  /* ==========================================================================
     11. INICIALIZACION
     ========================================================================== */
  initTheme();
  initNavigation();
  initLightbox();
  initMachineLearningSimulator();
  initEssayToc();
  loadConcepts();
});
