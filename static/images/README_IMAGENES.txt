GUIA DE GESTION DE IMAGENES PARA EL GLOSARIO DE IA
========================================================================

1. RUTA PRINCIPAL DE IMAGENES
------------------------------------------------------------------------
Coloca todas tus imagenes en este mismo directorio:
  static/images/

En la aplicacion web y al desplegar en servidores (Render, Railway, Heroku, etc.),
Flask servira directamente estos archivos de forma automatica y optimizada.


2. FORMATOS Y DIMENSIONES RECOMENDADAS
------------------------------------------------------------------------
- Formatos soportados: .jpg, .jpeg, .png, .webp, .svg
- Proporcion recomendada: 16:9 (o 4:3)
- Resolucion optima: 800 x 450 px (o 1200 x 675 px para pantallas de alta densidad)
- Peso recomendado por archivo: Entre 80 KB y 400 KB para velocidad de carga instantanea.


3. NOMBRES EXACTOS DE ARCHIVO POR CONCEPTO (20 CONCEPTOS)
------------------------------------------------------------------------
Asegurate de nombrar tus archivos con los siguientes nombres exactos:

01. Redes Neuronales Artificiales:
    01_redes_neuronales.jpg

02. Aprendizaje Profundo:
    02_deep_learning.jpg

03. Modelos de Lenguaje Grande:
    03_llm.jpg

04. Arquitectura Transformer:
    04_transformer.jpg

05. Mecanismo de Autoatencion:
    05_self_attention.jpg

06. Aprendizaje Supervisado:
    06_aprendizaje_supervisado.jpg

07. Aprendizaje No Supervisado:
    07_aprendizaje_no_supervisado.jpg

08. Aprendizaje por Refuerzo:
    08_aprendizaje_refuerzo.jpg

09. RLHF (Refuerzo con Feedback Humano):
    09_rlhf.jpg

10. Vision por Computadora:
    10_vision_computadora.jpg

11. Procesamiento del Lenguaje Natural:
    11_nlp.jpg

12. Modelos de Difusion:
    12_modelos_difusion.jpg

13. Redes Generativas Antagonicas:
    13_gans.jpg

14. Generacion Aumentada por Recuperacion:
    14_rag.jpg

15. Incrustaciones Vectoriales:
    15_embeddings.jpg

16. Agentes Autonomos y Multi-Agente:
    16_agentes_inteligentes.jpg

17. Alucinacion en Modelos de Lenguaje:
    17_alucinacion.jpg

18. Ajuste Fino y LoRA:
    18_fine_tuning.jpg

19. Descenso de Gradiente y Retropropagacion:
    19_descenso_gradiente.jpg

20. Sobreajuste y Regularizacion:
    20_sobreajuste.jpg


4. SISTEMA DE RESPALDO AUTOMATICO (FALLBACK)
------------------------------------------------------------------------
Si dejas conceptos sin imagen o mientras preparas tus archivos graficos,
el sistema detecta la ausencia fisica del archivo y renderiza de forma
automatica un diseno geometrico y vectorial de respaldo con la paleta de
colores oficial de la plataforma (dorado y verde azulado).
En cuanto coloques la imagen correspondiente en static/images/, la aplicacion
la cargara de inmediato sin necesidad de reiniciar la base de datos.
