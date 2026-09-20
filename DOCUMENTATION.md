# Documentacion Tecnica y Arquitectura del Sistema: Inteligencia Artificial

Este documento describe la arquitectura, las decisiones de diseno, la estructura de la base de datos, el catalogo de los 20 conceptos tecnicos, las secciones historicas y taxonomicas, y los procedimientos de despliegue para la aplicacion web de Inteligencia Artificial.

---

## 1. Resumen General del Sistema

El proyecto es una aplicacion web full-stack desarrollada en **Python** utilizando el microframework **Flask** y una base de datos relacional **SQLite**. Integra tres modulos centrales articulados mediante una barra de navegacion fija:

1. **Antecedentes Historicos**: Cronologia analitica de 10 hitos seminales (desde la *Ars Magna* de Ramon Llull en 1305 hasta la Conferencia de Dartmouth en 1956) acompasada por su infografia de alta resolucion ampliable mediante visor Lightbox.
2. **Clasificacion Clasica de la IA**: Explicacion teorica de la taxonomia tripartita (**ANI**, **AGI**, **ASI**) complementada con estudios de caso reales y prospectivos acompanados de sus respectivas infografias tecnicas:
   - **ANI (Inteligencia Artificial Estrecha)**: Caso de estudio real *AlphaFold y el plegamiento de proteinas* (Premio Nobel de Quimica 2024).
   - **AGI (Inteligencia Artificial General)**: Caso de estudio proyectado *Coordinacion global ante una pandemia emergente*.
   - **ASI (Superinteligencia Artificial)**: Caso de estudio proyectado *Aceleracion de la solucion al cambio climatico* y dilemas de alineacion.
3. **Glosario de Conceptos Clave**: Repositorio relacional de 20 conceptos tecnicos fundamentales con busqueda directa en tiempo real, perspectiva dinamica (3D Tilt) y modal para fichas tecnicas profundas.
4. **Buscador Global Inteligente**: Ubicado de manera permanente en la barra superior; al escribir un termino desde cualquier seccion, activa automaticamente el Glosario y filtra los conceptos en tiempo real.

---

## 2. Decisiones de Arquitectura

### 2.1 Backend: Python, Flask y SQLite
- **Flask**: Microframework liviano, de respuesta instantanea y facil despliegue en entornos PaaS y contenedores WSGI mediante Gunicorn.
- **SQLite embebido (`glossary.db`)**: 
  - Almacena de forma relacional y estructurada los 20 conceptos tecnicos con indices en `category` y `slug`.
  - Mecanismo de **auto-inicializacion y siembra automatica** (`ensure_database_ready()` en `app.py`), permitiendo despliegues limpios en servidores en la nube sin requerir comandos de terminal manuales posteriores.

### 2.2 Gestion de Activos e Infografias
- **Ruta física**: `static/images/`
- **Ruta pública**: `/static/images/<nombre_archivo>`
- **Infografias incorporadas**:
  - `timeline_antecedentes.png`: Infografia completa de la linea de tiempo historica.
  - `clasificacion_ani.jpg`: Infografia tecnica del estudio de caso de ANI con AlphaFold.
  - `clasificacion_agi.jpg`: Infografia del caso prospectivo de AGI ante pandemias.
  - `clasificacion_asi.jpg`: Infografia del caso prospectivo de ASI frente al cambio climatico.
- **Visor Lightbox de Alta Definicion**:
  - Componente modal en JavaScript vanilla que permite abrir e inspeccionar cualquier infografia a pantalla completa con scroll fluido para leer texto de tamano pequeno.
- **Mecanismo de Respaldo (Fallback)** para conceptos del glosario:
  - Si un concepto aun no tiene imagen fisica, se genera un diseno geometrico vectorial en SVG adaptado a la categoria correspondiente.

### 2.3 Depuracion y Limpieza Visual
- **Remocion del rotulo "Compendio de IA"**: La barra superior ahora se enfoca estrictamente en las tres opciones de navegacion (`Antecedentes`, `Clasificacion Clasica de la IA`, `Glosario`) y sus herramientas globales.
- **Remocion de la barra horizontal de categorias**: Se elimino la hilera de botones de categorias y la barra de desplazamiento horizontal para evitar ruido visual y brindar acceso directo a la cuadricula de conceptos.

### 2.4 Frontend: Diseno Editorial e Interacciones 3D
- **Tipografias**: *Fraunces* (fuente con serifas de contraste editorial para titulares) e *IBM Plex Sans* (fuente humanista optimizada para legibilidad en pantalla). Para codigo y formulas matematicas se emplea *IBM Plex Mono*.
- **Paleta Cromatica Institucional**: Tonos crema (`#EDEFEA`), tinta profunda (`#1E2A33`), acentos en oro viejo (`#A9752E`) y verde azulado (`#2F6F63`).
- **Modo Claro / Oscuro**: Totalmente funcional y persistente mediante `localStorage` y media query `prefers-color-scheme`.
- **Inclinacion 3D (Tilt)**: Calculo matricial en tiempo real que aplica `rotateX` y `rotateY` proporcionales a las coordenadas del raton dentro de la tarjeta, junto con un resplandor dinamico de iluminacion especular (`--glare-x`, `--glare-y`).
- **Ausencia de emojis**: Estricto cumplimiento del requerimiento de no emplear emojis en interfaces, codigo o documentacion.

---

## 3. Catalogo de los 20 Conceptos de IA en el Glosario

1. Redes Neuronales Artificiales (ANN)
2. Aprendizaje Profundo (Deep Learning)
3. Modelos de Lenguaje Grande (LLMs)
4. Arquitectura Transformer
5. Mecanismo de Autoatencion (Self-Attention)
6. Aprendizaje Supervisado
7. Aprendizaje No Supervisado
8. Aprendizaje por Refuerzo (RL)
9. RLHF (Refuerzo con Feedback Humano)
10. Vision por Computadora (CV)
11. Procesamiento del Lenguaje Natural (NLP)
12. Modelos de Difusion
13. Redes Generativas Antagonicas (GANs)
14. RAG (Generacion Aumentada por Recuperacion)
15. Incrustaciones Vectoriales (Embeddings)
16. Agentes Autonomos y Sistemas Multi-Agente
17. Alucinacion en Modelos de Lenguaje
18. Ajuste Fino y LoRA (Fine-Tuning)
19. Descenso de Gradiente y Retropropagacion (Backpropagation)
20. Sobreajuste y Regularizacion (Overfitting & Dropout)

---

## 4. Endpoints de la API REST

- `GET /`: Renderizado de la pagina web unificada.
- `GET /api/concepts`: Listado filtrable de conceptos (`search`, `favorites`).
- `GET /api/concepts/<int:id>`: Detalle de ficha tecnica profunda.
- `POST /api/concepts/<int:id>/favorite`: Alternador del estado de favorito.

---

## 5. Instrucciones de Despliegue en Produccion

### Despliegue en Render / Railway / Heroku
1. Empujar el codigo a un repositorio Git.
2. Configurar el servicio web:
   - **Comando de construccion**: `pip install -r requirements.txt`
   - **Comando de inicio**: `gunicorn app:app`
3. El archivo `Procfile` y las variables de puerto (`PORT`) son detectadas de manera automatica. La base de datos se inicializa y siembra en el primer arranque.

### Ejecucion Local en Windows
Hacer doble clic en `run.bat` o ejecutar:
```powershell
pip install -r requirements.txt
python app.py
```
Abrir `http://localhost:5000` en el navegador web.
