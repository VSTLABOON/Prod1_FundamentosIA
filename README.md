# Compendio de Inteligencia Artificial: Antecedentes, Taxonomia, Algoritmos de Busqueda, Chatbot ML for Kids, Machine Learning, Glosario y Etica

Aplicacion web full-stack academica construida en **Python (Flask + SQLite)** y **JavaScript Vanilla** bajo un diseno editorial limpio y libre de ruido visual. Permite explorar la evolucion historica de la Inteligencia Artificial, su clasificacion clasica, los paradigmas de busqueda formal con un **Chatbot Clasificador y Argumentador impulsado por Machine Learning for Kids (4 etiquetas)**, fundamentos y simulacion matematica de Machine Learning, un glosario relacional de 20 conceptos tecnicos con interaccion 3D y un ensayo academico integro sobre etica de la IA.

---

## Tabla de Contenidos

1. [Resumen General del Sistema](#1-resumen-general-del-sistema)
2. [Modulos y Secciones Principales](#2-modulos-y-secciones-principales)
3. [Arquitectura del Chatbot ML for Kids (4 Etiquetas y Desambiguacion Discursiva)](#3-arquitectura-del-chatbot-ml-for-kids-4-etiquetas-y-desambiguacion-discursiva)
4. [Simulador Matematico de Inferencia en Machine Learning](#4-simulador-matematico-de-inferencia-en-machine-learning)
5. [Arquitectura de Base de Datos y Catalogo de 20 Conceptos](#5-arquitectura-de-base-de-datos-y-catalogo-de-20-conceptos)
6. [Especificacion Completa de la API REST](#6-especificacion-completa-de-la-api-rest)
7. [Estructura Completa del Proyecto](#7-estructura-completa-del-proyecto)
8. [Sistema de Diseno Editorial Academico y Frontend](#8-sistema-de-diseno-editorial-academico-y-frontend)
9. [Instalacion y Ejecucion Local](#9-instalacion-y-ejecucion-local)
10. [Despliegue en Produccion (Cloud PaaS)](#10-despliegue-en-produccion-cloud-paas)

---

## 1. Resumen General del Sistema

El proyecto integra en una sola plataforma interactiva seis secciones tematicas y herramientas transversales accesibles desde una barra de navegacion superior persistente:

- **Backend**: Microframework **Flask** (`app.py`), motor de base de datos relacional **SQLite** (`database.py`, `seed_db.py`) con auto-inicializacion automatica al arrancar, y motor de lenguaje natural y clasificacion supervisada **ML for Kids** (`ml_chatbot.py`).
- **Frontend**: Plantillas modulares **Jinja2** (`templates/components/` y `templates/sections/`), arquitectura CSS modularizada en 10 hojas de estilo (`static/css/modules/`) y controlador interactivo en JavaScript (`static/js/app.js`).
- **Principios Visuales**: Estetica editorial universitaria con tipografias *Fraunces*, *IBM Plex Sans* e *IBM Plex Mono*, soporte nativo para **Modo Claro y Modo Oscuro**, diseno 100% responsivo y **ausencia total de emojis** o barras de porcentaje innecesarias.

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

### 2.7 Herramientas Globales Transversales
- **Buscador Global Inteligente (`#globalSearchInput`)**: Al escribir desde cualquier pestaña del sitio, conmuta automaticamente al Glosario y filtra los conceptos en tiempo real.
- **Acceso Directo al Chatbot ML (`#chatbotNavBtn`)**: Lleva directamente a la consola del clasificador ML for Kids y enfoca el campo de texto.
- **Modo Quiz / Autoevaluacion (`#quizToggleBtn`)**: Genera cuestionarios dinamicos de opcion multiple basados en la base de datos SQLite con retroalimentacion inmediata y conteo de aciertos.

---

## 3. Arquitectura del Chatbot ML for Kids (4 Etiquetas y Desambiguacion Discursiva)

El modulo [`ml_chatbot.py`](ml_chatbot.py) y su interfaz [`templates/components/chatbot_ml.html`](templates/components/chatbot_ml.html) implementan un sistema de clasificacion de texto y argumentacion academica entrenado especificamente con **4 etiquetas**:

| Etiqueta | Dominio Conceptual | Indicadores Principales |
| :--- | :--- | :--- |
| **`Heuristica`** | Busqueda Informada / Heuristica | $A^*$, $IDA^*$, Busqueda Voraz (*Greedy Best-First*), funciones de evaluacion $f(n)=g(n)+h(n)$, heuristica admisible y consistente, distancia Manhattan / Euclidiana. |
| **`Ciega`** | Busqueda No Informada / A Ciegas | BFS (anchura, cola FIFO), DFS (profundidad, pila LIFO), Costo Uniforme (UCS), Profundizacion Iterativa (IDDFS), exploracion exhaustiva sin funcion heuristica ($h(n)=0$). |
| **`Evolutiva`** | Busqueda Evolutiva y Metaheuristicas | Algoritmos Geneticos (AG), poblacion de cromosomas, funcion de aptitud (*fitness*), seleccion por torneo/ruleta, cruza (*crossover*), mutacion, PSO, ACO. |
| **`Desconocido`** | Fuera de Dominio / Saludos / Trampas Coloquiales | Saludos, preguntas generales de la plataforma, temas ajenos (cocina, deportes, clima, redes neuronales generales) y **frases trampa coloquiales** donde aparecen palabras como *"a ciegas"* o *"evolucion"* fuera del contexto de algoritmos de busqueda. |

### 3.1 Soporte Dual: Sin Cuenta en ML for Kids y Con Cuenta (Cloud API)

1. **Modo Sin Cuenta (Activo por defecto y con Entrenador en Vivo)**:
   - En `machinelearningforkids.co.uk`, cuando se elige *"Probar sin registrarse"*, el proyecto se guarda en el `localStorage` del navegador (`#!/mlproject/localstorage/...`) y ML for Kids no genera una API Key en la nube para Python.
   - Para garantizar que funcione sin cuenta desde el primer instante, [`LocalMLForKidsClassifier`](ml_chatbot.py) entrena en memoria un clasificador supervisado Bayesiano Multinomial + N-gramas sobre un corpus curado de **80 ejemplos base** (20 por cada una de las 4 cubetas).
   - Ademas, el panel **`Configurar / Entrenar Modelo`** en la interfaz web permite **agregar nuevos ejemplos de texto a cualquiera de las 4 cubetas y reentrenar el modelo en vivo** (`POST /api/chatbot/train`), replicando exactamente la experiencia de entrenamiento de ML for Kids sin necesidad de registrarse.
   - Si el usuario pega por error la URL del navegador de un proyecto sin cuenta (`https://machinelearningforkids.co.uk/#!/mlproject/localstorage/...`), la funcion `extract_mlforkids_key()` detecta el marcador `__BROWSER_LOCALSTORAGE__` y muestra un aviso explicativo manteniendo activo el motor local sin errores.
2. **Modo Con Cuenta (API Key en la Nube de ML for Kids)**:
   - Si se ingresa una API Key o URL de API de una cuenta registrada de ML for Kids, el sistema consulta directamente el endpoint oficial `https://machinelearningforkids.co.uk/api/scratch/<KEY>/classify` y combina su veredicto con el motor de analisis discursivo para construir el argumento.

### 3.2 Motor de Desambiguacion Discursiva para Menciones Multiples

Uno de los requerimientos centrales es **clasificar correctamente incluso cuando el usuario menciona los 3 algoritmos (`Heuristica`, `Ciega` y `Evolutiva`) dentro de un mismo parrafo**. Para lograrlo sin confundirse por el simple conteo de palabras, [`ml_chatbot.py`](ml_chatbot.py) ejecuta un pipeline de 4 etapas:

1. **Segmentacion en Clausulas Discursivas (`split_into_discourse_clauses`)**:
   - Divide la oracion compuesta en sub-clausulas utilizando signos de puntuacion, conectores adversativos (*pero, sin embargo, no obstante, sino, en cambio, mientras que*), conectores concesivos (*aunque, a pesar de que, si bien*), marcadores de descarte (*a diferencia de, en lugar de, en vez de, descartando, dejando de lado*), transiciones sin coma (*"A diferencia de la busqueda ciega y la evolutiva usamos A*"*) y comparaciones de superioridad (*"es mejor que", "es mas rapida que"*).
2. **Asignacion de Rol Pragmatico (`analyze_clause_discourse_role`)**:
   - Cada clausula recibe un rol y un multiplicador de peso:
     - `foco_principal` (peso `+2.35`): Clausula introducida por un conector adversativo fuerte (*pero, sino, por ello elegimos*), pregunta directa (*"¿cual...?"*) o afirmacion de uso (*"implementamos", "utilizamos", "es mejor"*).
     - `afirmado` (peso `+1.25`): Clausula declarativa estandar que describe el funcionamiento del algoritmo principal.
     - `concesivo` (peso `-0.65`): Clausula subordinada que menciona un algoritmo solo como contraste secundario (*"Aunque la busqueda ciega..."*).
     - `descartado` (peso `-1.45`): Clausula con negacion explicita o preposicion de exclusion (*"A diferencia de los algoritmos geneticos...", "no usamos BFS"*).
3. **Deteccion de Definiciones por Ausencia de Heuristica (`BLIND_ABSENCE_OF_HEURISTIC_REGEX`)**:
   - Si el texto dice *"explora el grafo sin usar una funcion heuristica"* o *"no utiliza conocimiento adicional del dominio"*, el motor reconoce que la negacion de heuristica es precisamente la definicion formal de **Busqueda Ciega (`Ciega`)**, asignandole puntaje positivo a `Ciega` y enmascarando el fragmento para no activar falsamente `Heuristica`.
4. **Filtro de Usos Coloquiales No Algoritmicos (`NON_ALGORITHMIC_COLLOQUIAL_PATTERNS`)**:
   - Frases como *"Confio a ciegas en mi equipo"* o *"La evolucion del rock en los anos 80"* son interceptadas antes de puntuar `Ciega` o `Evolutiva`, clasificandose correctamente como **`Desconocido`**.

### 3.3 Generador Contextual y Dinamico de Argumentos (Sin Frases Frias ni Porcentajes)

En lugar de devolver respuestas pre-programadas rigidas o saturar la vista con barras de porcentaje, [`generate_specific_insight()`](ml_chatbot.py) y [`build_verdict_argument()`](ml_chatbot.py) construyen una respuesta estructurada en tres bloques limpios:

1. **Argumento de Seleccion**: Explica por que se asigno la etiqueta ganadora citando los indicadores exactos detectados en el mensaje del usuario y adaptando la redaccion segun la intencion (pregunta teorica, caso practico de ingenieria, comparacion, saludo o frase coloquial fuera de dominio).
2. **Resolucion de Menciones Multiples** *(se muestra cuando el texto menciona 2 o mas paradigmas)*: Cita textualmente en que fragmento el usuario afirmo el algoritmo ganador y en que fragmento descarto o contrasto los otros algoritmos mencionados.
3. **Analisis Especifico**: Adapta la explicacion al sub-algoritmo y escenario concreto mencionado por el usuario (por ejemplo, navegacion GPS con $A^*$, memoria exponencial en BFS, backtracking en DFS, optimalidad por costo acumulado en UCS, combinacion de ambos en IDDFS, o evolucion poblacional mediante cruza y mutacion en Algoritmos Geneticos).

---

## 4. Simulador Matematico de Inferencia en Machine Learning

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

## 5. Arquitectura de Base de Datos y Catalogo de 20 Conceptos

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

## 6. Especificacion Completa de la API REST

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

---

## 7. Estructura Completa del Proyecto

```text
Prod1/
|-- app.py                          # Servidor Flask, rutas web, endpoints API REST y auto-seed de BD
|-- ml_chatbot.py                   # Clasificador ML for Kids (4 etiquetas), desambiguador discursivo y generador de argumentos
|-- database.py                     # Capa de persistencia SQLite, consultas parametrizadas y generador de Quiz
|-- seed_db.py                      # Corpus de datos de los 20 conceptos tecnicos de IA
|-- glossary.db                     # Base de datos relacional SQLite (generada/verificada automaticamente)
|-- requirements.txt                # Dependencias de Python (Flask==3.0.3, gunicorn==22.0.0)
|-- Procfile                        # Declaracion de proceso WSGI para despliegue cloud (web: gunicorn app:app)
|-- runtime.txt                     # Especificacion de version de Python para plataformas PaaS
|-- run.bat                         # Script automatizado para crear entorno virtual, instalar paquetes y arrancar en Windows
|-- DOCUMENTATION.md                # Documento complementario de arquitectura
|-- README.md                       # Documentacion maestra integral del proyecto
|
|-- static/
|   |-- css/
|   |   |-- style.css               # Hoja de estilo maestra que importa los 10 modulos CSS
|   |   |-- style.backup.css        # Copia de respaldo de estilos
|   |   `-- modules/                # Arquitectura CSS modular por dominio
|   |       |-- base.css            # Variables CSS (Modo Claro/Oscuro), reset y tipografia editorial
|   |       |-- navbar.css          # Barra de navegacion superior fija, buscador global y controles
|   |       |-- antecedentes.css    # Linea del tiempo historica y tarjetas cronologicas
|   |       |-- clasificacion.css   # Tarjetas comparativas ANI, AGI, ASI y casos de estudio
|   |       |-- busqueda.css        # Formulas matematicas, tablas A*, paradigmas y consola del Chatbot ML
|   |       |-- machine_learning.css# Pipeline de 5 fases y simulador interactivo de fraude
|   |       |-- glosario.css        # Cuadricula 3D Tilt de los 20 conceptos y tarjetas vectoriales
|   |       |-- ensayo.css          # Maquetacion editorial del ensayo academico e indice lateral
|   |       |-- modals.css          # Modales de fichas tecnicas, cuestionario Quiz y visor Lightbox
|   |       `-- responsive.css      # Reglas de adaptacion para pantallas medianas, tablets y moviles
|   |-- js/
|   |   `-- app.js                  # Controlador frontend: navegacion, buscador, 3D tilt, lightbox, quiz, simulador ML y chatbot
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
    |   |-- chatbot_ml.html         # Interfaz del Chatbot ML for Kids, chips de prueba y entrenador de 4 cubetas
    |   |-- modal_concept.html      # Modal de ficha tecnica detallada de cada concepto del glosario
    |   |-- modal_lightbox.html     # Visor de alta resolucion para inspeccionar infografias
    |   `-- footer.html             # Pie de pagina institucional
    `-- sections/                   # Secciones principales de contenido
        |-- antecedentes.html       # Seccion 1: Antecedentes de la IA
        |-- clasificacion.html      # Seccion 2: Clasificacion Clasica (ANI, AGI, ASI)
        |-- busqueda.html           # Seccion 3: Algoritmos de Busqueda + Chatbot ML for Kids
        |-- machine_learning.html   # Seccion 4: Machine Learning + Simulador en Tiempo Real
        |-- glosario.html           # Seccion 5: Glosario Interactivo de 20 Conceptos
        `-- ensayo.html             # Seccion 6: Ensayo Academico sobre Etica de la IA
```

---

## 8. Sistema de Diseno Editorial Academico y Frontend

- **Tipografia Jerarquica**:
  - Titulares y encabezados academicos: `'Fraunces'` (serifa de alto contraste editorial).
  - Cuerpo de lectura e interfaz: `'IBM Plex Sans'` (optima legibilidad en bloques extensos).
  - Expresiones matematicas, complejidad algoritmica y etiquetas tecnicas: `'IBM Plex Mono'`.
- **Paleta Cromatica con Soporte Dual (Claro / Oscuro)**:
  - **Modo Claro**: Papel crema calido (`#EDEFEA`), superficies blancas (`#F7F8F5`), tinta profunda (`#1E2A33`), acento dorado academico (`#A9752E`) y verde azulado (`#2F6F63`).
  - **Modo Oscuro**: Pizarra nocturna (`#11161B`), superficies elevadas (`#192129`), texto marfil (`#E6EAE8`), acento ambar (`#DF9B42`) y turquesa suave (`#4DB09E`).
- **Diferenciacion Cromatica de las 4 Etiquetas del Chatbot**:
  - `Heuristica`: Verde azulado (`--accent-teal`).
  - `Ciega`: Azul pizarra academico (`#3b6e8c`).
  - `Evolutiva`: Oro viejo (`--accent-gold`).
  - `Desconocido`: Gris neutro editorial (`--text-muted`).

---

## 9. Instalacion y Ejecucion Local

### Opcion A: Inicio Rapido en Windows
Hacer doble clic sobre el archivo [`run.bat`](run.bat). El script creara automaticamente el entorno virtual `venv` (si no existe), instalara las dependencias de `requirements.txt`, verificara la base de datos SQLite e iniciara el servidor en `http://localhost:5000`.

### Opcion B: Ejecucion Manual por Terminal
```powershell
# 1. Crear y activar entorno virtual (opcional pero recomendado)
python -m venv venv
.\venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Iniciar la aplicacion
python app.py
```
Abrir el navegador en **`http://localhost:5000`**.

---

## 10. Despliegue en Produccion (Cloud PaaS)

El proyecto esta listo para desplegarse sin configuracion adicional en **Render**, **Railway**, **Heroku** o cualquier entorno compatible con WSGI:

1. **Dependencias de Produccion**: Incluidas en [`requirements.txt`](requirements.txt) (`Flask==3.0.3`, `gunicorn==22.0.0`).
2. **Comando de Arranque**: Definido en [`Procfile`](Procfile):
   ```text
   web: gunicorn app:app
   ```
3. **Auto-Inicializacion**: Al importar `app:app`, Gunicorn ejecuta automaticamente `ensure_database_ready()` (creando y poblando `glossary.db` si el contenedor es efimero) y pre-entrena en memoria el clasificador `LOCAL_CLASSIFIER` de `ml_chatbot.py`.
