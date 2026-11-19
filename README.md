# Compendio de Inteligencia Artificial: Antecedentes, Taxonomia, Algoritmos de Busqueda, Brazo Robotico 3D, Chatbot ML for Kids, Machine Learning, Glosario y Etica

Aplicacion web full-stack academica construida en **Python (Flask + SQLite)**, **Three.js (WebGL 3D)** y **JavaScript Vanilla** bajo un diseno editorial limpio y libre de ruido visual. Permite explorar la evolucion historica de la Inteligencia Artificial, su clasificacion clasica, los paradigmas de busqueda formal con un **Simulador de Almacen 2D**, un **Simulador de Brazo Robotico 3D en Celda Automotriz con Bitacora SQL, Memoria de Rutas (CBR) y Mini-RAG**, un **Chatbot Clasificador y Argumentador impulsado por Machine Learning for Kids (4 etiquetas)**, fundamentos y simulacion matematica de Machine Learning, un glosario relacional de 20 conceptos tecnicos con interaccion 3D y un ensayo academico integro sobre etica de la IA.

---

## Tabla de Contenidos

1. [Resumen General del Sistema](#1-resumen-general-del-sistema)
2. [Modulos y Secciones Principales](#2-modulos-y-secciones-principales)
3. [Brazo Robotico 3D: C-Space, 8 Movimientos, Margen de 900, SQL y Mini-RAG](#3-brazo-robotico-3d-c-space-8-movimientos-margen-de-900-sql-y-mini-rag)
4. [Arquitectura del Chatbot ML for Kids (4 Etiquetas y Desambiguacion Discursiva)](#4-arquitectura-del-chatbot-ml-for-kids-4-etiquetas-y-desambiguacion-discursiva)
5. [Simulador Matematico de Inferencia en Machine Learning](#5-simulador-matematico-de-inferencia-en-machine-learning)
6. [Arquitectura de Base de Datos y Catalogo de 20 Conceptos](#6-arquitectura-de-base-de-datos-y-catalogo-de-20-conceptos)
7. [Especificacion Completa de la API REST](#7-especificacion-completa-de-la-api-rest)
8. [Estructura Completa del Proyecto](#8-estructura-completa-del-proyecto)
9. [Sistema de Diseno Editorial Academico, Modales y Responsividad](#9-sistema-de-diseno-editorial-academico-modales-y-responsividad)
10. [Instalacion, Pruebas y Ejecucion Local](#10-instalacion-pruebas-y-ejecucion-local)
11. [Despliegue en Produccion (Cloud PaaS / Render)](#11-despliegue-en-produccion-cloud-paas--render)

---

## 1. Resumen General del Sistema

El proyecto integra en una sola plataforma interactiva siete secciones tematicas y herramientas transversales accesibles desde una barra de navegacion superior persistente:

- **Backend**: Microframework **Flask** (`app.py`), motor de base de datos relacional **SQLite** (`database.py`, `seed_db.py`, `arm_storage.py`) con auto-inicializacion y migracion automatica al arrancar, motor de planificacion cinematica e inversa en espacio de configuraciones (`robot_arm_search.py`), y paquete modular de lenguaje natural y clasificacion supervisada **ML for Kids** (`chatbot/`, con fachada de compatibilidad en `ml_chatbot.py`).
- **Frontend**: Plantillas modulares **Jinja2** (`templates/components/` y `templates/sections/`), arquitectura CSS modularizada en 12 hojas de estilo (`static/css/modules/`) y controladores interactivos en JavaScript (`static/js/app.js`, `static/js/search_visualizer.js`, `static/js/brazo_robotico.js`).
- **Principios Visuales**: Estetica editorial universitaria con tipografias *Fraunces*, *IBM Plex Sans* e *IBM Plex Mono*, soporte nativo para **Modo Claro y Modo Oscuro**, modales de altura acotada (`dvh`) con scroll interno aislado y bloqueo de desplazamiento de fondo, diseno 100% responsivo y **ausencia total de emojis**.

---

## 2. Modulos y Secciones Principales

### 2.1 Antecedentes Historicos (`templates/sections/antecedentes.html`)
- Linea del tiempo analitica con **10 hitos seminales** desde el *Ars Magna* de Ramon Llull (1305) hasta la Conferencia de Dartmouth (1956), pasando por Leibniz, Boole, Babbage, Ada Lovelace, Russell & Whitehead, Gödel, Turing, McCulloch & Pitts y Wiener.
- Infografia oficial de alta resolucion (`static/images/timeline_antecedentes.png`) con apertura en visor **Lightbox** a pantalla completa.

### 2.2 Clasificacion Clasica de la IA (`templates/sections/clasificacion.html`)
- Desarrollo conceptual y comparativo de los tres niveles de capacidad:
  1. **ANI (Inteligencia Artificial Estrecha)**: Caso de estudio real *AlphaFold y el plegamiento de proteinas* (Premio Nobel de Quimica 2024) con infografia (`clasificacion_ani.jpg`).
  2. **AGI (Inteligencia Artificial General)**: Caso de estudio prospectivo *Coordinacion global ante una pandemia emergente* con infografia (`clasificacion_agi.jpg`).
  3. **ASI (Superinteligencia Artificial)**: Caso de estudio prospectivo *Aceleracion de la solucion al cambio climatico y dilemas de alineacion* con infografia (`clasificacion_asi.jpg`).

### 2.3 Algoritmos de Busqueda y Optimizacion (`templates/sections/busqueda.html`)
- **Formulacion Matematica del Problema de Busqueda**: Definicion de la 6-tupla formal $P = \langle S, s_0, A(s), \text{Result}(s,a), \text{GoalTest}(s), c(s,a,s') \rangle$.
- **Caso Practico Resuelto Paso a Paso**: Calculo de la ruta optima **Puebla -> Ciudad de Mexico** utilizando el algoritmo $A^*$ con funcion de evaluacion $f(n) = g(n) + h(n)$, tabla de distancias en linea recta y traza completa de expansion de nodos.
- **Infografia Dedicada**: Visualizacion de alta definicion (`algoritmos_busqueda.png`).
- **Taxonomia de Paradigmas de Busqueda**:
  - *Busqueda Ciega (No Informada)*: BFS (colas FIFO), DFS (pilas LIFO), Costo Uniforme (UCS / Dijkstra) y Profundizacion Iterativa (IDDFS).
  - *Busqueda Heuristica (Informada)*: Busqueda Voraz Primero el Mejor, $A^*$, $IDA^*$, y demostracion de las propiedades de **Admisibilidad** ($0 \le h(n) \le h^*(n)$) y **Consistencia / Monotonicidad** ($h(n) \le c(n,a,n') + h(n')$).
  - *Busqueda Local*: Escalada de Colinas (Hill Climbing), Recocido Simulado (Simulated Annealing) y Busqueda Tabu con memoria $O(1)$.
  - *Busqueda Evolutiva y Metaheuristicas Poblacionales*: Algoritmos Geneticos (poblacion, funcion de aptitud / fitness, seleccion por torneo/ruleta, cruza y mutacion), Enjambre de Particulas (PSO) y Colonia de Hormigas (ACO).
- **Tabla Comparativa de Complejidad**: Completitud, optimalidad, complejidad temporal y complejidad espacial en funcion de $b$ (factor de ramificacion), $d$ (profundidad de la solucion optima) y $m$ (profundidad maxima).
- **Consola del Chatbot Clasificador ML for Kids**: Integrada en la seccion y accesible directamente desde el boton **`Chatbot ML`** de la barra de navegacion superior.

### 2.4 Machine Learning (`templates/sections/machine_learning.html`)
- Contraste formal entre la programacion clasica basada en reglas explicitas y el aprendizaje inductivo basado en datos.
- Explicacion de los 3 paradigmas fundamentales: **Aprendizaje Supervisado** (regresion y clasificacion), **Aprendizaje No Supervisado** (clustering y reduccion de dimensionalidad) y **Aprendizaje por Refuerzo** (procesos de decision de Markov, agente, entorno y recompensa).
- **Pipeline Integral de 5 Fases**: Recoleccion y curacion de datos, Ingenieria de caracteristicas (*Feature Engineering*), Entrenamiento y optimizacion de parametros, Evaluacion y validacion cruzada, e Inferencia y monitoreo en produccion.
- **Simulador Interactivo de Deteccion de Fraude en Tiempo Real**: Permite ajustar variables de una transaccion bancaria y observar en vivo el calculo del logit $z = \mathbf{w}^T\mathbf{x} + b$ y la probabilidad mediante la funcion sigmoide $\sigma(z) = \frac{1}{1 + e^{-z}}$.

### 2.5 Glosario Relacional de 20 Conceptos (`templates/sections/glosario.html`)
- Cuadricula de tarjetas con efecto de perspectiva tridimensional (**3D Tilt**) e iluminacion especular dinamica.
- Filtro de busqueda instantanea en tiempo real, filtro de conceptos **Favoritos** persistente en SQLite y modal de ficha tecnica profunda (`templates/components/modal_concept.html`) con definicion extendida, importancia, ejemplo practico, palabras clave y conceptos relacionados navegables.

### 2.6 Ensayo Academico de Etica en la IA (`templates/sections/ensayo.html`)
- Texto integro del ensayo *"Etica y aspectos sociales de la inteligencia artificial"* (**Barranco Cervantes Jesus Manuel**, Universidad Tecnologica de Puebla, Grupo 7°C, Septiembre 2026).
- Indice lateral interactivo con seguimiento de lectura (*scroll-spy*) a lo largo de los 14 capitulos tematicos, analisis de la tesis de las tres condiciones inseparables (finalidad legitima, evidencia verificable y mecanismos de reparacion), tabla comparativa del dilema de asignacion de becas (Grupos A y B) y referencias bibliograficas en formato APA.

### 2.7 Brazo Robotico 3D en Celda Automotriz (`templates/sections/brazo_robotico.html`)
- Simulacion industrial interactiva en **Three.js (WebGL 3D)** sincronizada en tiempo real con el **Espacio de Configuraciones (C-Space 2D)** de $72 \times 72 = 5{,}184$ posturas posibles.
- Ejecucion de tareas practicas multi-etapa (*Pick & Place*, *Soldar Puerta (3 pts)* y *Pasillo Estrecho*), arrastre en vivo de obstaculos y puntos objetivo en el escenario 3D, inyeccion de **obstaculo imprevisto** con replanificacion al vuelo, **HUD de telemetria angular** (`Hombro X° · Codo Y°`) y comparador simultaneo de 5 algoritmos (**A\***, **Costo Uniforme**, **Busqueda Voraz**, **Anchura BFS** y **Profundidad DFS**).
- Integracion de **Bitacora SQL**, **Memoria de Rutas (CBR)** y **Consultor Mini-RAG** en lenguaje natural sobre `glossary.db`.

### 2.8 Herramientas Globales Transversales
- **Buscador Global Inteligente (`#globalSearchInput`)**: Al escribir desde cualquier pestaña del sitio, conmuta automaticamente al Glosario y filtra los conceptos en tiempo real.
- **Acceso Directo al Chatbot ML (`#chatbotNavBtn`)**: Lleva directamente a la consola del clasificador ML for Kids y enfoca el campo de texto.
- **Modo Quiz / Autoevaluacion (`#quizToggleBtn`)**: Genera cuestionarios dinamicos de opcion multiple basados en la base de datos SQLite con retroalimentacion inmediata y conteo de aciertos.

---

## 3. Brazo Robotico 3D: C-Space, 8 Movimientos, Margen de 900, SQL y Mini-RAG

El modulo [`robot_arm_search.py`](robot_arm_search.py) modela formalmente un brazo robotico planar de 2 grados de libertad (eslabon de hombro $L_1 = 95\text{ px}$ y eslabon de codo/antorcha $L_2 = 80\text{ px}$) dentro de una celda de manufactura automotriz:

- **Espacio de Estados ($S$)**: Cuadricula toroidal discreta de $(\theta_1, \theta_2) \in [0^\circ, 360^\circ)^2$ en pasos de `STEP_DEG = 5` grados ($72 \times 72 = 5{,}184$ estados).
- **Acciones en 8 Direcciones ($A(s)$) y Costo Energetico ($c(s,a,s')$)**:
  - 4 movimientos ortogonales (una sola articulacion): giro de hombro ($\pm 5^\circ$, costo `COST_SHOULDER = 1.6`) o giro de codo ($\pm 5^\circ$, costo `COST_ELBOW = 1.0`).
  - 4 movimientos diagonales simultaneos (hombro + codo a la vez): costo `COST_DIAG = 1.9` ($\approx \sqrt{1.6^2 + 1.0^2}$) con validacion anti-cruce de esquinas de colision.
- **Heuristica Octil Admisible ($h(n)$)**: `angular_heuristic` calcula la distancia angular minima en el toro $72 \times 72$ hacia el conjunto de posturas meta combinando pasos diagonales (`1.9`) y pasos ortogonales restantes (`1.6` o `1.0`), garantizando optimalidad en $A^*$.
- **Margen Operativo Esperado (`EXPECTED_MAX_EXPANSIONS = 900`) y Bandera `within_budget`**:
  - `900` posturas representan aproximadamente el **17%** del espacio total de $5{,}184$ configuraciones (el presupuesto esperado por etapa para una busqueda informada en condiciones normales).
  - Los algoritmos exploratorios cuentan con un tope duro ampliado (`MAX_DFS_EXPANSIONS = 2400`, `MAX_GREEDY_EXPANSIONS = 2200`). Si una estrategia completa la tarea pero supera las `900` posturas en alguna etapa (por ejemplo, **DFS** en *Pick & Place* con `1,294` posturas, o **Costo Uniforme** / **BFS**), se registra con `within_budget = False` y la interfaz la señala como **Fuera de expectativas (>900)**. Si el propio **A\*** requiere superar 900 en geometrias concavas estrechas (*Soldar Puerta* o *Pasillo Estrecho*), se conserva como **Optima** indicando que es el minimo matematico posible.
- **Persistencia en SQLite y Mini-RAG ([`arm_storage.py`](arm_storage.py))**:
  - Tabla `arm_runs`: Bitacora de corridas con metricas (`nodes_expanded`, `energy`, `cycle_seconds`, `had_unexpected`, `from_cache`, `within_budget`, `cargo_id`, `cargo_name`, `weight_kg`, `delivered`, `payload_energy_tax`, `transport_distance_m`), geometria serializada para **Cargar escena** en 3D y documento indexado para recuperacion.
  - Tabla `arm_cargo_ledger`: Inventario de **Carga Transportada** en planta (lote, pieza: *Modulo Bateria EV 18 kg*, *Bastidor de Puerta 12 kg* o *Modulo LiDAR 5 kg*, estacion origen $\to$ destino, distancia recorrida en metros con pinza cerrada, sobrecarga energetica por torque y estado `entregado` / `abortado_en_ruta` / `sin_recoger`).
  - Tabla `arm_route_cache`: Memoria de rutas exitosa indexada por huella SHA-256 (`scene_hash`, `algorithm_id`) que recupera trayectorias repetidas en ~`0.8 ms` sin reexplorar.
  - **Mini-RAG Local (`query_arm_rag`)**: Motor de recuperacion y sintesis en Python sobre `arm_runs` y `arm_cargo_ledger` que responde preguntas en lenguaje natural sobre fallos, ahorro energetico, imprevistos, piezas entregadas (`kg` y metros) y corridas fuera del margen de 900 posturas.

---

## 4. Arquitectura del Chatbot ML for Kids (4 Etiquetas y Desambiguacion Discursiva)

Todo el codigo de Python dedicado exclusivamente al chatbot ha sido estructurado de forma modular e independiente dentro de la carpeta [`chatbot/`](chatbot/README.md), manteniendo [`ml_chatbot.py`](ml_chatbot.py) como fachada de compatibilidad hacia atras e integrando su interfaz en [`templates/components/chatbot_ml.html`](templates/components/chatbot_ml.html):

| Etiqueta | Dominio Conceptual | Indicadores Principales |
| :--- | :--- | :--- |
| **`Heuristica`** | Busqueda Informada / Heuristica (100 ejemplos de entrenamiento) | $A^*$, $IDA^*$, Busqueda Voraz (*Greedy Best-First*), funciones de evaluacion $f(n)=g(n)+h(n)$, heuristica admisible y consistente, distancia Manhattan / Euclidiana. |
| **`Ciega`** | Busqueda No Informada / A Ciegas (120 ejemplos de entrenamiento) | BFS (anchura, cola FIFO), DFS (profundidad, pila LIFO), Costo Uniforme (UCS), Profundizacion Iterativa (IDDFS), exploracion exhaustiva sin funcion heuristica ($h(n)=0$). |
| **`Evolutiva`** | Busqueda Evolutiva y Metaheuristicas (90 ejemplos de entrenamiento) | Algoritmos Geneticos (AG), poblacion de cromosomas, funcion de aptitud (*fitness*), seleccion por torneo/ruleta, cruza (*crossover*), mutacion, PSO, ACO. |
| **`Desconocido`** | Fuera de Dominio / Ciencias de la Computacion / Saludos (110 ejemplos) | Saludos, ordenamiento clasico, busqueda binaria, grafos generales, bases de datos SQL, redes TCP/IP y **frases trampa coloquiales** donde aparecen palabras como *"a ciegas"* o *"evolucion"* fuera de algoritmos de busqueda en IA. |

### 3.1 Estructura Modular del Paquete `chatbot/`

El paquete [`chatbot/`](chatbot/README.md) se compone de modulos especializados con responsabilidad unica:
- **`chatbot/corpus.py`**: Corpus oficial con **420 enunciados de entrenamiento** (100 Heuristica, 120 Ciega, 90 Evolutiva, 110 Desconocido).
- **`chatbot/classifier.py`**: Normalizacion de texto, expresiones regulares de dominio (`DOMAIN_PATTERNS`), clasificador local Naive Bayes multinomial con N-gramas (`LocalMLForKidsClassifier`) y cliente HTTP para la API en la nube de ML for Kids.
- **`chatbot/discourse.py`**: Segmentador discursivo (`split_into_discourse_clauses`) y analizador pragmatico de roles (`analyze_clause_discourse_role`).
- **`chatbot/argumentation.py`**: Generador de explicaciones vivas y argumentos contextuales (`build_verdict_argument`, `generate_specific_insight`).
- **`chatbot/engine.py`**: Pipeline unificado (`classify_message`) que conecta todos los modulos.
- **`chatbot/cli.py`**: Interfaz de terminal y evaluador de precision (`python -m chatbot.cli --test` reporta 420/420, 100% de precision).
- **`chatbot/__init__.py`**: Fachada de exportacion publica del paquete.

### 3.2 Soporte Dual: Sin Cuenta en ML for Kids y Con Cuenta (Cloud API)

1. **Modo Sin Cuenta (Activo por defecto y con Entrenador en Vivo)**:
   - En `machinelearningforkids.co.uk`, cuando se elige *"Probar sin registrarse"*, el proyecto se guarda en el `localStorage` del navegador (`#!/mlproject/localstorage/...`) y ML for Kids no genera una API Key en la nube para Python.
   - Para garantizar que funcione sin cuenta desde el primer instante, [`LocalMLForKidsClassifier`](chatbot/classifier.py) entrena en memoria un clasificador supervisado Bayesiano Multinomial + N-gramas sobre el corpus oficial de **420 ejemplos**.
   - Ademas, el panel **`Configurar / Entrenar Modelo`** en la interfaz web permite **agregar nuevos ejemplos de texto a cualquiera de las 4 cubetas y reentrenar el modelo en vivo** (`POST /api/chatbot/train`), replicando exactamente la experiencia de entrenamiento de ML for Kids sin necesidad de registrarse.
   - Si el usuario pega por error la URL del navegador de un proyecto sin cuenta (`https://machinelearningforkids.co.uk/#!/mlproject/localstorage/...`), la funcion `extract_mlforkids_key()` detecta el marcador `__BROWSER_LOCALSTORAGE__` y muestra un aviso explicativo manteniendo activo el motor local sin errores.
2. **Modo Con Cuenta (API Key en la Nube de ML for Kids)**:
   - Si se ingresa una API Key o URL de API de una cuenta registrada de ML for Kids, el sistema consulta directamente el endpoint oficial `https://machinelearningforkids.co.uk/api/scratch/<KEY>/classify` y combina su veredicto con el motor de analisis discursivo para construir el argumento.

### 3.3 Motor de Desambiguacion Discursiva para Menciones Multiples

Uno de los requerimientos centrales es **clasificar correctamente incluso cuando el usuario menciona los 3 algoritmos (`Heuristica`, `Ciega` y `Evolutiva`) dentro de un mismo parrafo**. Para lograrlo sin confundirse por el simple conteo de palabras, [`chatbot/discourse.py`](chatbot/discourse.py) y [`chatbot/engine.py`](chatbot/engine.py) ejecutan un pipeline de 4 etapas:

1. **Segmentacion en Clausulas Discursivas (`split_into_discourse_clauses`)**:
   - Divide la oracion compuesta en sub-clausulas utilizando signos de puntuacion, conectores adversativos (*pero, sin embargo, no obstante, sino, en cambio, mientras que*), conectores concesivos (*aunque, a pesar de que, si bien*), marcadores de descarte (*a diferencia de, en lugar de, en vez de, descartando, dejando de lado*), transiciones sin coma (*"A diferencia de la busqueda ciega y la evolutiva usamos A*"*) y comparaciones de superioridad (*"es mejor que", "es mas rapida que"*).
2. **Asignacion de Rol Pragmatico (`analyze_clause_discourse_role`)**:
   - Cada clausula recibe un rol y un multiplicador de peso:
     - `foco_principal` (peso `2.50`): Clausula introducida por un conector adversativo fuerte (*pero, sino, por ello elegimos*), pregunta directa (*"¿cual...?"*) o afirmacion de uso (*"implementamos", "utilizamos", "es mejor"*).
     - `afirmacion` (peso `1.00`): Clausula declarativa estandar que describe el funcionamiento del algoritmo principal.
     - `concesion_previa` (peso `0.22`): Premisa previa que queda superada por la conclusion final tras el conector (*pero / por eso*).
     - `contexto_comparativo` (peso `0.18`): Clausula que solo enumera las opciones antes de lanzar la pregunta principal.
     - `contraste_o_negacion` (peso `0.06 - 0.12`): Exclusion deliberada (*"en lugar de", "sin usar", "descartando"*).
3. **Deteccion de Definiciones por Ausencia de Heuristica (`BLIND_ABSENCE_OF_HEURISTIC_REGEX`)**:
   - Si el texto dice *"explora el grafo sin usar una funcion heuristica"* o *"no utiliza conocimiento adicional del dominio"*, el motor reconoce que la negacion de heuristica es precisamente la definicion formal de **Busqueda Ciega (`Ciega`)**, asignandole puntaje positivo a `Ciega` y enmascarando el fragmento para no activar falsamente `Heuristica`.
4. **Filtro de Usos Coloquiales y Temas Ajenos (`COLLOQUIAL_TRICK_PATTERNS`)**:
   - Frases como *"Confio a ciegas en mi equipo"* o temas de ingenieria general (ordenamiento, bases de datos SQL, redes TCP/IP) son clasificados con precision en **`Desconocido`**.

### 3.4 Generador Contextual y Dinamico de Argumentos (Sin Frases Frias ni Porcentajes)

En lugar de devolver respuestas pre-programadas rigidas o saturar la vista con barras de porcentaje, [`generate_specific_insight()`](chatbot/argumentation.py) y [`build_verdict_argument()`](chatbot/argumentation.py) construyen una respuesta estructurada en tres bloques limpios:

1. **Argumento de Seleccion**: Explica por que se asigno la etiqueta ganadora citando los indicadores exactos detectados en el mensaje del usuario y adaptando la redaccion segun la intencion (pregunta teorica, caso practico de ingenieria, comparacion, saludo o frase coloquial fuera de dominio).
2. **Resolucion de Menciones Multiples** *(se muestra cuando el texto menciona 2 o mas paradigmas)*: Cita textualmente en que fragmento el usuario afirmo el algoritmo ganador y en que fragmento descarto o contrasto los otros algoritmos mencionados.
3. **Analisis Especifico**: Adapta la explicacion al sub-algoritmo y escenario concreto mencionado por el usuario (por ejemplo, navegacion GPS con $A^*$, memoria exponencial en BFS, backtracking en DFS, optimalidad por costo acumulado en UCS, combinacion de ambos en IDDFS, o evolucion poblacional mediante cruza y mutacion en Algoritmos Geneticos).

---

## 5. Simulador Matematico de Inferencia en Machine Learning

Ubicado en la seccion **Machine Learning** (`templates/sections/machine_learning.html` y controlado en `static/js/app.js`), permite experimentar en tiempo real con un modelo de **Regresion Logistica Binaria** entrenado para deteccion de fraude en transacciones financieras:

- **Variables de Entrada ($\mathbf{x}$)**:
  - $x_1$: Monto de la transaccion (USD).
  - $x_2$: Distancia geografica respecto al domicilio habitual (km).
  - $x_3$: Hora de la operacion (horario nocturno / inusual).
  - $x_4$: Frecuencia de intentos en los ultimos 10 minutos.
- **Calculo en Tiempo Real**:
  1. Normalizacion de caracteristicas y producto punto con el vector de pesos $\mathbf{w}$ mas el sesgo $b$:
     $$z = w_1 \hat{x}_1 + w_2 \hat{x}_2 + w_3 \hat{x}_3 + w_4 \hat{x}_4 + b$$
  2. Activacion mediante la funcion sigmoide:
     $$P(\text{Fraude} \mid \mathbf{x}) = \sigma(z) = \frac{1}{1 + e^{-z}}$$
  3. Clasificacion automatica segun el umbral de decision ($\tau = 0.50$) con desglose matematico visible paso a paso.

---

## 6. Arquitectura de Base de Datos y Catalogo de 20 Conceptos

El motor [`database.py`](database.py) gestiona la base de datos SQLite (`glossary.db`) con inicializacion automatica e idempotente desde [`seed_db.py`](seed_db.py).

### 5.1 Esquema de la Tabla `concepts`

| Columna | Tipo | Descripcion |
| :--- | :--- | :--- |
| `id` | `INTEGER PRIMARY KEY AUTOINCREMENT` | Identificador unico del concepto. |
| `term` | `TEXT NOT NULL` | Nombre oficial del concepto en espanol e ingles. |
| `slug` | `TEXT NOT NULL UNIQUE` | Identificador URL-safe indexado (`idx_concepts_slug`). |
| `category` | `TEXT NOT NULL` | Categoria taxonomica indexada (`idx_concepts_category`). |
| `short_definition` | `TEXT NOT NULL` | Sintesis conceptual mostrada en la tarjeta del glosario. |
| `full_definition` | `TEXT NOT NULL` | Explicacion tecnica profunda mostrada en el modal. |
| `why_it_matters` | `TEXT NOT NULL` | Relevancia cientifica e industrial del concepto. |
| `example` | `TEXT NOT NULL` | Caso de aplicacion real y concreto. |
| `image_filename` | `TEXT NOT NULL` | Nombre del archivo grafico asociado en `static/images/`. |
| `keywords` | `TEXT NOT NULL` | Arreglo JSON serializado de palabras clave tecnicas. |
| `related_terms` | `TEXT NOT NULL` | Arreglo JSON serializado de conceptos vinculados. |
| `is_favorite` | `INTEGER DEFAULT 0` | Estado booleano (`0` o `1`) para el filtro de favoritos. |

### 5.2 Los 20 Conceptos Tecnicos Incluidos

1. **Redes Neuronales Artificiales (ANN)**
2. **Aprendizaje Profundo (Deep Learning)**
3. **Modelos de Lenguaje Grande (LLMs)**
4. **Arquitectura Transformer**
5. **Mecanismo de Autoatencion (Self-Attention)**
6. **Aprendizaje Supervisado**
7. **Aprendizaje No Supervisado**
8. **Aprendizaje por Refuerzo (RL)**
9. **RLHF (Aprendizaje por Refuerzo con Retroalimentacion Humana)**
10. **Vision por Computadora (Computer Vision)**
11. **Procesamiento del Lenguaje Natural (NLP)**
12. **Modelos de Difusion (Diffusion Models)**
13. **Redes Generativas Antagonicas (GANs)**
14. **RAG (Generacion Aumentada por Recuperacion)**
15. **Incrustaciones Vectoriales (Embeddings)**
16. **Agentes Autonomos y Sistemas Multi-Agente**
17. **Alucinacion en Modelos de Lenguaje**
18. **Ajuste Fino y LoRA (Fine-Tuning)**
19. **Descenso de Gradiente y Retropropagacion (Backpropagation)**
20. **Sobreajuste y Regularizacion (Overfitting & Dropout)**

---

## 7. Especificacion Completa de la API REST

Todos los endpoints estan definidos en [`app.py`](app.py) y devuelven respuestas en formato JSON UTF-8.

### 6.1 Glosario y Evaluacion

- **`GET /`**
  Renderiza la aplicacion completa inyectando los conceptos, categorias y estadisticas iniciales en [`templates/index.html`](templates/index.html).
- **`GET /api/concepts`**
  Filtra conceptos por texto o estado de favorito.
  - Parametros query opcionales: `search` (texto), `category` (nombre o `all`), `favorites` (`true`/`false`).
- **`GET /api/concepts/<int:concept_id>`**
  Devuelve la ficha tecnica completa de un concepto especifico junto con su estado de imagen (`has_custom_image` e `image_url`).
- **`POST /api/concepts/<int:concept_id>/favorite`**
  Alterna el estado `is_favorite` del concepto en SQLite y devuelve el nuevo valor booleano.
- **`GET /api/categories`**
  Retorna el listado de categorias y el conteo de conceptos por cada una.
- **`GET /api/quiz?limit=5`**
  Genera un cuestionario aleatorio de seleccion multiple (entre 1 y 15 preguntas) a partir de los conceptos de la base de datos.

### 6.2 Chatbot ML for Kids

- **`POST /api/chatbot/classify`**
  Clasifica un mensaje en una de las 4 etiquetas (`Heuristica`, `Ciega`, `Evolutiva`, `Desconocido`), ejecuta la desambiguacion de menciones multiples y devuelve el argumento estructurado.
  - **Payload JSON**:
    ```json
    {
      "text": "Aunque la busqueda ciega como BFS explora por niveles y los algoritmos geneticos usan mutacion, para este GPS implementamos A* con distancia Manhattan.",
      "api_key": ""
    }
    ```
  - **Respuesta JSON**:
    ```json
    {
      "status": "success",
      "data": {
        "label": "Heuristica",
        "source": "mlforkids_trained_model",
        "mentioned_labels": ["Heuristica", "Ciega", "Evolutiva"],
        "discarded_labels": ["Ciega", "Evolutiva"],
        "is_multi_mention": true,
        "argument": {
          "title": "Busqueda Heuristica (Informada)",
          "main_reason": "Se selecciono la etiqueta **Heuristica** porque, tras analizar la estructura de tu oracion...",
          "multi_mention_analysis": "Tu texto hace referencia a **3 paradigmas distintos**...",
          "foundation": "En tu caso planteas un problema de navegacion y rutas con **A***..."
        }
      }
    }
    ```
- **`POST /api/chatbot/verify-key`**
  Verifica si una cadena ingresada es una API Key valida en la nube de ML for Kids, una URL de proyecto sin cuenta (`localstorage`) o si debe utilizarse el modelo local pre-entrenado.
- **`GET /api/chatbot/training-data`**
  Devuelve las 4 etiquetas oficiales y el corpus completo de entrenamiento (`TRAINING_CORPUS`) agrupado por cubeta.
- **`POST /api/chatbot/train`**
  Agrega un nuevo ejemplo de texto a cualquiera de las 4 cubetas (`Heuristica`, `Ciega`, `Evolutiva`, `Desconocido`) y reentrena en vivo el clasificador local.
  - **Payload JSON**:
    ```json
    {
      "label": "Heuristica",
      "text": "El algoritmo A* utiliza la heuristica Manhattan para guiar la busqueda hacia la meta"
    }
    ```

### 6.3 Planificador del Brazo Robotico 3D, Bitacora SQL y Mini-RAG

- **`GET /health`**
  Endpoint de verificacion de salud para Render (`{"status": "ok"}`).
- **`GET /api/arm/presets`**
  Devuelve la geometria del brazo, el catalogo de los 5 algoritmos, los 3 escenarios de una etapa (`PRESET_SCENARIOS`) y las 3 tareas practicas multi-etapa (`TASK_PRESETS`).
- **`POST /api/arm/solve`** y **`POST /api/arm/compare`**
  Resuelven o comparan los 5 algoritmos sobre un punto objetivo unico `(target_x, target_y)`.
- **`POST /api/arm/solve-sequence`**
  Resuelve una secuencia completa de puntos de trabajo (`waypoints`) con soporte de Memoria SQL (`use_memory`) y registro automatico en `arm_runs` (`record_run`), devolviendo `within_budget`, `budget_limit` (`900`), etapas, camino en C-Space y cuadros cinematicos.
- **`POST /api/arm/compare-sequence`**
  Ejecuta las 5 estrategias sobre la misma secuencia y obstáculos reutilizando el mapa de colisiones base en Python.
- **`GET /api/arm/history?filter=all|failed|unexpected&limit=40`**
  Devuelve KPIs agregados (`total_runs`, `total_failures`, `total_from_cache`, `astar_energy_savings_pct`), historial de corridas y entradas en `arm_route_cache`.
- **`DELETE /api/arm/history?scope=runs|cache|all`**
  Limpia la bitacora de corridas, la memoria de rutas o ambas tablas.
- **`POST /api/arm/rag`**
  Ejecuta el Mini-RAG local en Python sobre los registros de `arm_runs` para responder preguntas en lenguaje natural citando las corridas fuente y su similitud.

---

## 8. Estructura Completa del Proyecto

```text
Prod1/
|-- app.py                          # Servidor Flask, rutas web, endpoints API REST y auto-seed de BD
|-- robot_arm_search.py             # Motor C-Space (72x72), 8 movimientos, A*/UCS/Voraz/BFS/DFS y margen 900
|-- arm_storage.py                  # Persistencia SQLite (arm_runs, arm_route_cache) y motor Mini-RAG local
|-- test_robot_arm.py               # Suite unittest de cinematica, algoritmos, endpoints Flask, SQL y Mini-RAG
|-- ml_chatbot.py                   # Modulo de compatibilidad hacia atras (reexporta desde chatbot/)
|-- database.py                     # Capa de persistencia SQLite, consultas parametrizadas y generador de Quiz
|-- seed_db.py                      # Corpus de datos de los 20 conceptos tecnicos de IA
|-- glossary.db                     # Base de datos relacional SQLite (generada/verificada automaticamente)
|-- requirements.txt                # Dependencias de Python (Flask==3.0.3, gunicorn==22.0.0)
|-- Procfile                        # Declaracion de proceso WSGI para despliegue cloud (web: gunicorn app:app)
|-- runtime.txt                     # Especificacion de version de Python (python-3.11.9)
|-- run.bat                         # Script automatizado para crear entorno virtual, instalar paquetes y arrancar en Windows
|-- DOCUMENTATION.md                # Documento complementario de arquitectura
|-- README.md                       # Documentacion maestra integral del proyecto
|
|-- chatbot/                        # PAQUETE DEDICADO EXCLUSIVAMENTE AL CHATBOT ML FOR KIDS
|   |-- __init__.py                 # Fachada de exportacion publica del paquete
|   |-- corpus.py                   # Corpus oficial (420 enunciados / 4 etiquetas de entrenamiento)
|   |-- classifier.py               # Naive Bayes con N-gramas, patrones de dominio y cliente API
|   |-- discourse.py                # Segmentacion en clausulas y analisis retorico de intencion
|   |-- argumentation.py            # Generador de explicaciones vivas y argumentos contextuales
|   |-- engine.py                   # Orquestador del pipeline principal (classify_message)
|   |-- cli.py                      # CLI interactivo y suite de benchmarks (python -m chatbot.cli --test)
|   `-- README.md                   # Documentacion tecnica detallada del paquete chatbot
|
|-- static/
|   |-- css/
|   |   |-- style.css               # Hoja de estilo maestra que importa los 12 modulos CSS en orden de cascada
|   |   |-- style.backup.css        # Copia de respaldo de estilos
|   |   `-- modules/                # Arquitectura CSS modular por dominio
|   |       |-- base.css            # Variables CSS (Modo Claro/Oscuro), reset y tipografia editorial
|   |       |-- navbar.css          # Barra de navegacion superior fija, buscador global y controles
|   |       |-- modals.css          # Modales base, pestañas con flex-shrink:0, cuestionario Quiz y Lightbox
|   |       |-- antecedentes.css    # Linea del tiempo historica y tarjetas cronologicas
|   |       |-- clasificacion.css   # Tarjetas comparativas ANI, AGI, ASI y casos de estudio
|   |       |-- busqueda.css        # Formulas matematicas, tablas A*, paradigmas y consola del Chatbot ML
|   |       |-- search_visualizer.css # Simulador interactivo 2D de robot de surtido en almacen y modal compacto
|   |       |-- machine_learning.css# Pipeline de 5 fases y simulador interactivo de fraude
|   |       |-- glosario.css        # Cuadricula 3D Tilt de los 20 conceptos y tarjetas vectoriales
|   |       |-- ensayo.css          # Maquetacion editorial del ensayo academico e indice lateral
|   |       |-- brazo_robotico.css  # Escena 3D Three.js, mapa C-Space, HUDs y modales con scroll interno aislado
|   |       `-- responsive.css      # Reglas de adaptacion para pantallas medianas, tablets y moviles
|   |-- js/
|   |   |-- app.js                  # Controlador frontend: navegacion, buscador, 3D tilt, lightbox, quiz, simulador ML y chatbot
|   |   |-- search_visualizer.js    # Controlador del simulador 2D de almacen
|   |   `-- brazo_robotico.js       # Controlador Three.js 3D, C-Space interactivo, modales comparativos y Bitacora SQL/RAG
|   `-- images/
|       |-- timeline_antecedentes.png # Infografia de antecedentes historicos (1305 - 1956)
|       |-- clasificacion_ani.jpg     # Infografia del caso de estudio ANI (AlphaFold)
|       |-- clasificacion_agi.jpg     # Infografia del caso de estudio AGI (Respuesta a pandemias)
|       |-- clasificacion_asi.jpg     # Infografia del caso de estudio ASI (Cambio climatico)
|       |-- algoritmos_busqueda.png   # Infografia tecnica de Algoritmos de Busqueda
|       `-- README_IMAGENES.txt       # Guia de nomenclatura para activos visuales adicionales
|
`-- templates/
    |-- index.html                  # Plantilla raiz que ensambla componentes y secciones
    |-- index.backup.html           # Respaldo de plantilla monolitica previa
    |-- components/                 # Componentes transversales reutilizables
    |   |-- navbar.html             # Barra superior con pestañas, buscador global, boton Chatbot ML, Quiz y Tema
    |   |-- search_visualizer.html  # Componente interactivo de busqueda en almacen 2D
    |   |-- chatbot_ml.html         # Interfaz del Chatbot ML for Kids, chips de prueba y entrenador de 4 cubetas
    |   |-- modal_concept.html      # Modal de ficha tecnica detallada de cada concepto del glosario
    |   |-- modal_lightbox.html     # Visor de alta resolucion para inspeccionar infografias
    |   `-- footer.html             # Pie de pagina institucional
    `-- sections/                   # Secciones principales de contenido
        |-- antecedentes.html       # Seccion 1: Antecedentes de la IA
        |-- clasificacion.html      # Seccion 2: Clasificacion Clasica (ANI, AGI, ASI)
        |-- busqueda.html           # Seccion 3: Algoritmos de Busqueda + Simulador Almacen + Chatbot ML
        |-- brazo_robotico.html     # Seccion 4: Brazo Robotico 3D + C-Space + Modales Comparativo y SQL/RAG
        |-- machine_learning.html   # Seccion 5: Machine Learning + Simulador en Tiempo Real
        |-- glosario.html           # Seccion 6: Glosario Interactivo de 20 Conceptos
        `-- ensayo.html             # Seccion 7: Ensayo Academico sobre Etica de la IA
```

---

## 9. Sistema de Diseno Editorial Academico, Modales y Responsividad

- **Tipografia Jerarquica**:
  - Titulares y encabezados academicos: `'Fraunces'` (serifa de alto contraste editorial).
  - Cuerpo de lectura e interfaz: `'IBM Plex Sans'` (optima legibilidad en bloques extensos).
  - Expresiones matematicas, complejidad algoritmica y etiquetas tecnicas: `'IBM Plex Mono'`.
- **Paleta Cromatica con Soporte Dual (Claro / Oscuro)**:
  - **Modo Claro**: Papel crema calido (`#EDEFEA`), superficies blancas (`#F7F8F5`), tinta profunda (`#1E2A33`), acento dorado academico (`#A9752E`) y verde azulado (`#2F6F63`).
  - **Modo Oscuro**: Pizarra nocturna (`#11161B`), superficies elevadas (`#192129`), texto marfil (`#E6EAE8`), acento ambar (`#DF9B42`) y turquesa suave (`#4DB09E`).
- **Arquitectura de Modales sin Doble Scroll (`dvh` + `arm-modal-lock`)**:
  - `modules/modals.css` se importa antes de los modulos especializados para garantizar cascada limpia.
  - Los modales tienen altura acotada al viewport dinamico (`max-height: min(85dvh, ...)` / `height: min(78dvh, 540px)` en `#armLogModal`), cabeceras y barras de pestañas fijas (`flex-shrink: 0; overflow-y: hidden;`), bloqueo del scroll de fondo (`html.arm-modal-lock, body.arm-modal-lock`) y una unica region interna desplazable (`overscroll-behavior: contain`).
  - En `#armCompareModal`, las 5 tarjetas de algoritmos se organizan en cuadricula compacta de 2 columnas en escritorio (con el ganador **A\*** a ancho completo arriba) para evitar scroll innecesario, pasando a 1 columna con barras de 2 columnas en moviles (`<= 640px`).

---

## 10. Instalacion, Pruebas y Ejecucion Local

### Opcion A: Inicio Rapido en Windows
Hacer doble clic sobre el archivo [`run.bat`](run.bat). El script creara automaticamente el entorno virtual `venv` (si no existe), instalara las dependencias de `requirements.txt`, verificara la base de datos SQLite e iniciara el servidor en `http://localhost:5000`.

### Opcion B: Ejecucion Manual y Suite de Pruebas por Terminal
```powershell
# 1. Crear y activar entorno virtual (opcional pero recomendado)
python -m venv venv
.\venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar pruebas unitarias y de integracion (Brazo Robotico 3D, SQL, RAG y Chatbot)
python -m unittest test_robot_arm.py -v
python -m chatbot.cli --test

# 4. Iniciar la aplicacion
python app.py
```
Abrir el navegador en **`http://localhost:5000`**.

---

## 11. Despliegue en Produccion (Cloud PaaS / Render)

El proyecto esta listo para desplegarse sin configuracion adicional en **Render**, **Railway**, **Heroku** o cualquier entorno compatible con WSGI:

1. **Dependencias de Produccion**: Incluidas en [`requirements.txt`](requirements.txt) (`Flask==3.0.3`, `gunicorn==22.0.0`).
2. **Comando de Arranque**: Definido en [`Procfile`](Procfile):
   ```text
   web: gunicorn app:app
   ```
3. **Auto-Inicializacion**: Al importar `app:app`, Gunicorn ejecuta automaticamente `ensure_database_ready()` (creando y poblando `glossary.db` si el contenedor es efimero) y pre-entrena en memoria el clasificador `LOCAL_CLASSIFIER` de `ml_chatbot.py`.
