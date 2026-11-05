# Paquete Chatbot ML for Kids (`chatbot/`)

Modulo especializado en Python para la clasificacion y argumentacion pedagogica de consultas sobre algoritmos de Inteligencia Artificial utilizando la tecnologia y convencion de **Machine Learning for Kids (ML for Kids)**.

---

## 1. Vision General

Este paquete encapsula todo el codigo Python dedicado exclusivamente a:
1. **Clasificar** textos en una de las 4 etiquetas oficiales:
   - `Heuristica` (Busqueda Informada: A*, Hill Climbing, Simulated Annealing, Beam Search, IDA*, etc.)
   - `Ciega` (Busqueda No Informada: BFS, DFS, UCS, DLS, IDDFS, Bidireccional)
   - `Evolutiva` (Busqueda Bioinspirada: Algoritmos Geneticos, Estrategias Evolutivas, Programacion Genetica, NSGA-II)
   - `Desconocido` (Ciencias de la Computacion fuera de busqueda en IA, frases coloquiales y saludos)
2. **Resolver consultas multi-mencion**: Si el usuario redacta un parrafo donde se citan las tres categorias al mismo tiempo (ej: *"Aunque conozco BFS y se que los algoritmos geneticos cruzan cromosomas, para este mapa con GPS prefiero usar el algoritmo A\* con distancia Manhattan"*), el analizador discursivo descompone las clausulas, identifica el objetivo central y descarta las menciones accesorias.
3. **Generar un argumento conversacional fundamentado**: Proporciona una explicacion detallada, viva y pedagogica de por que se eligio la etiqueta y como se relaciona con el planteamiento del usuario, evitando respuestas frias o genericas.
4. **Soportar tanto el modelo local integrado como endpoints de ML for Kids en la nube**: Funciona de inmediato sin necesidad de cuenta externa, y permite enlazar una API Key de Scratch/Python de ML for Kids cuando se disponga de una.

---

## 2. Arquitectura de Archivos

```
chatbot/
│
├── __init__.py           # Exporta la interfaz publica unificada
├── corpus.py             # Corpus oficial con 420 enunciados etiquetados
├── classifier.py         # Naive Bayes multinomial con N-gramas, patrones de dominio y cliente API
├── discourse.py          # Segmentacion en clausulas y analisis retorico de intencion
├── argumentation.py      # Generacion de argumentos explicativos y justificaciones tecnicas
├── engine.py             # Pipeline orquestador principal (classify_message)
├── cli.py                # Interfaz de terminal y evaluador de precision (benchmark)
└── README.md             # Esta documentacion
```

---

## 3. Descripcion de Modulos

### 3.1 `chatbot/corpus.py`
- Define las listas oficiales `LABELS` y `ALGORITHM_LABELS`.
- Contiene el diccionario `TRAINING_CORPUS` con **420 enunciados de entrenamiento**:
  - `Heuristica`: 100 ejemplos
  - `Ciega`: 120 ejemplos
  - `Evolutiva`: 90 ejemplos
  - `Desconocido`: 110 ejemplos

### 3.2 `chatbot/classifier.py`
- `normalize_text(text)`: Limpieza minuscula, remocion de tildes y diacriticos.
- `extract_mlforkids_key(raw_input)`: Extraccion robusta de API Key desde strings, URLs o codigo copiado.
- `canonicalize_label(raw_label)`: Homogeneizacion de etiquetas variantes a los 4 nombres oficiales.
- `LocalMLForKidsClassifier`: Implementacion local reentrenable en vivo de clasificador Naive Bayes multinomial enriquecido con N-gramas (unigramas, bigramas, trigramas) y evaluacion de patrones tecnicos de dominio (`DOMAIN_PATTERNS`).
- `check_mlforkids_status(key)`: Comprobacion de conectividad con servidores remotos de ML for Kids.
- `query_mlforkids_api(key, text)`: Consulta HTTP directa a los endpoints Scratch de Machine Learning for Kids.

### 3.3 `chatbot/discourse.py`
- `split_into_discourse_clauses(text)`: Segmenta parrafos complejos reconociendo conjunciones adversativas (*"pero"*, *"sin embargo"*), concesivas (*"aunque"*, *"si bien"*), restrictivas (*"a diferencia de"*, *"en lugar de"*, *"sin usar"*) y delimitadores sintacticos.
- `analyze_clause_discourse_role(clause, index, total, all_clauses)`: Pondera cada fragmento segun su funcion retorica:
  - `foco_principal` (factor 2.50)
  - `afirmacion` (factor 1.00)
  - `concesion_previa` (factor 0.22)
  - `contexto_comparativo` (factor 0.18)
  - `contraste_o_negacion` (factor 0.06 - 0.12)

### 3.4 `chatbot/argumentation.py`
- `generate_specific_insight(focal_text, full_text, winning_label)`: Identifica los conceptos y operadores exactos mencionados (ej. A*, Manhattan, Recocido Simulado, Hill Climbing, BFS, DLS, IDDFS, crossover PMX, etc.) y genera una explicacion conceptual precisa.
- `build_verdict_argument(...)`: Construye el objeto de respuesta con estructura clara: veredicto principal, analisis de descarte multi-mencion y aplicacion al caso planteado.

### 3.5 `chatbot/engine.py`
- `classify_message(text, api_key=None)`: Funcion principal de entrada que orquesta el analisis discursivo, la clasificacion Naive Bayes, la fusion con la nube (si hay API key) y la generacion del argumento pedagogico.

### 3.6 `chatbot/cli.py`
- Punto de entrada para pruebas directas desde terminal y ejecucion de benchmarks.

---

## 4. Modo de Uso

### Desde Python
```python
import chatbot

# Clasificacion estandar
resultado = chatbot.classify_message("El algoritmo A* con distancia Manhattan")
print("Etiqueta:", resultado["label"])
print("Argumento:\n", resultado["response"])

# Consulta con multi-mencion
consulta = (
    "Entre BFS, los algoritmos geneticos y A*, en este proyecto "
    "usaremos A* porque contamos con la distancia euclidiana."
)
res = chatbot.classify_message(consulta)
print("Veredicto:", res["label"])  # Heuristica
print("Algoritmos detectados:", res["mentioned_algorithms"])
```

### Desde la Terminal (CLI)
```bash
# 1. Ejecutar evaluacion del corpus completo (420 ejemplos)
python -m chatbot.cli --test

# 2. Iniciar sesion interactiva en consola
python -m chatbot.cli

# 3. Clasificar una oracion especifica
python -m chatbot.cli "La cola FIFO de la busqueda en anchura expande nivel por nivel"
```

---

## 5. Pruebas y Rendimiento

El clasificador fue probado sobre el 100% de los 420 enunciados oficiales de entrenamiento:
- **Heuristica**: 100/100 (100.00%)
- **Ciega**: 120/120 (100.00%)
- **Evolutiva**: 90/90 (100.00%)
- **Desconocido**: 110/110 (100.00%)
- **Precision Global**: 420/420 (100.00%)
