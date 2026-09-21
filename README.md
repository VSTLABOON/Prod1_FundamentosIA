# Compendio de Inteligencia Artificial: Antecedentes, Clasificacion Clasica y Glosario

Aplicacion web full-stack construida en Python (Flask + SQLite) disenada para consultar la evolucion historica, la taxonomia clasica y 20 conceptos tecnicos clave de Inteligencia Artificial.

---

## Modulos Principales

1. **Barra de Navegacion Superior Persistente**:
   - `Antecedentes`: Linea del tiempo interactiva de 10 hitos seminales (1305 - 1956) e infografia en alta definicion.
   - `Clasificacion Clasica de la IA`: Analisis de ANI, AGI y ASI con casos de estudio reales y prospectivos acompanados de sus respectivas infografias tecnicas.
   - `Machine Learning`: Fundamentos del paradigma inductivo, los 3 grandes paradigmas (Supervisado, No Supervisado, Por Refuerzo), el pipeline de 5 fases y un simulador interactivo de inferencia matematica en tiempo real para deteccion de fraude.
   - `Glosario`: Repositorio relacional de 20 conceptos tecnicos con cuadricula de tarjetas 3D Tilt y modal de fichas tecnicas profundas.
2. **Buscador Global Inteligente**:
   - Ubicado en la barra superior. Al escribir cualquier termino desde cualquier seccion, activa automaticamente el Glosario y filtra los conceptos en tiempo real.
3. **Visor Lightbox de Infografias**:
   - Permite ampliar e inspeccionar a pantalla completa las 4 infografias en alta definicion.
4. **Diseno Editorial Academico**:
   - Fuentes *Fraunces* e *IBM Plex Sans*, colores institucionales, transicion suave entre Modo Claro y Oscuro y total ausencia de emojis.

---

## Estructura del Proyecto

```
Prod1/
|-- app.py                     # Servidor Flask, API REST y auto-inicializacion de BD
|-- database.py                # Modelo relacional SQLite y consultas indexadas
|-- seed_db.py                 # Datos de los 20 conceptos tecnicos
|-- glossary.db                # Base de datos relacional SQLite
|-- requirements.txt           # Dependencias de produccion (Flask, gunicorn)
|-- Procfile                   # Comando de arranque para la nube
|-- runtime.txt                # Version de Python para despliegue
|-- run.bat                    # Script de inicio rapido en Windows
|-- DOCUMENTATION.md           # Documentacion tecnica de arquitectura y despliegue
|-- README.md                  # Este manual
|
|-- static/
|   |-- css/
|   |   `-- style.css          # Estilos editoriales, barra superior, 3D tilt, lightbox
|   |-- js/
|   |   `-- app.js             # Logica de navegacion, buscador global, lightbox, quiz
|   `-- images/
|       |-- timeline_antecedentes.png # Infografia de la linea de tiempo historica
|       |-- clasificacion_ani.jpg     # Infografia de ANI (AlphaFold)
|       |-- clasificacion_agi.jpg     # Infografia de AGI (Pandemias)
|       |-- clasificacion_asi.jpg     # Infografia de ASI (Cambio Climatico)
|       `-- README_IMAGENES.txt       # Guia para las imagenes de los 20 conceptos
|
`-- templates/
    `-- index.html             # Maquetacion semantica con las 3 secciones
```

---

## Ejecucion Local

Hacer doble clic en `run.bat` o ejecutar:
```powershell
pip install -r requirements.txt
python app.py
```
Abrir `http://localhost:5000` en el navegador web.
