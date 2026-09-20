"""
seed_db.py
Script de poblacion de datos para el Glosario de Inteligencia Artificial.

Inserta 20 conceptos tecnicos fundamentales con definiciones rigurosas,
ejemplos aplicados a la industria, detalles matematicos/arquitectonicos
y referencias a los nombres de archivo de imagen correspondientes en static/images/.

Excluye explicitamente terminos de taxonomia general (AGI, ASI, ANI, IA).
"""

from database import get_db_connection, init_db

CONCEPTS_DATA = [
    {
        "slug": "redes-neuronales-artificiales",
        "title": "Redes Neuronales Artificiales",
        "title_en": "Artificial Neural Networks (ANN)",
        "category": "Arquitecturas y Modelos",
        "difficulty": "Intermedio",
        "short_desc": "Modelos computacionales inspirados en circuitos biologicos compuestos por capas de nodos interconectados que ponderan senales de entrada.",
        "full_definition": "Una Red Neuronal Artificial es una estructura de procesamiento masivo en paralelo constituida por unidades simples denominadas neuronas artificiales. Estas unidades se organizan en una capa de entrada, una o multiples capas ocultas y una capa de salida. Cada conexion transmite una senal ponderada mediante pesos sinapticos, cuya combinacion lineal se transforma a traves de una funcion de activacion no lineal.",
        "real_world_example": "Clasificacion de patrones en electrocardiogramas para detectar arritmias cardiacas en tiempo real en dispositivos medicos de monitoreo.",
        "technical_detail": "Salida de un nodo: y = f(sum(w_i * x_i) + b), donde w_i representa los pesos sinapticos, x_i las entradas, b el sesgo y f la funcion de activacion (ReLU, Sigmoide, GELU).",
        "historical_milestone": "En 1958, Frank Rosenblatt desarrollo el Perceptron en el Laboratorio Aeronautico de Cornell, sentando las bases del conexionismo computacional.",
        "image_name": "01_redes_neuronales.jpg",
        "tags": "deep-learning, conexionismo, perceptron, capas"
    },
    {
        "slug": "aprendizaje-profundo",
        "title": "Aprendizaje Profundo",
        "title_en": "Deep Learning",
        "category": "Fundamentos de Aprendizaje",
        "difficulty": "Intermedio",
        "short_desc": "Subcampo del aprendizaje automatico basado en arquitecturas de representacion jerarquica con multiples capas no lineales sucesivas.",
        "full_definition": "El Aprendizaje Profundo comprende algoritmos que descubren automaticamente representaciones abstractas de datos sin necesidad de ingenieria manual de caracteristicas. A traves de decenas o cientos de capas de transformacion no lineal, los niveles inferiores detectan patrones primitivos (bordes, texturas) mientras que los niveles superiores construyen conceptos semanticos complejos.",
        "real_world_example": "Sistemas de navegacion autonoma de vehiculos que procesan transmisiones de camaras y sensores LiDAR para segmentar peatones, carriles y senales viales simultaneamente.",
        "technical_detail": "Minimizacion de la funcion de perdida empirica J(theta) mediante optimizadores estocasticos (Adam, SGD) propagando gradientes a traves de grafos computacionales profundos.",
        "historical_milestone": "En 2012, Alex Krizhevsky, Ilya Sutskever y Geoffrey Hinton presentaron AlexNet, superando por amplio margen a los metodos tradicionales en el concurso ImageNet.",
        "image_name": "02_deep_learning.jpg",
        "tags": "representacion-jerarquica, alexnet, redes-profundas, abstraccion"
    },
    {
        "slug": "modelos-de-lenguaje-grande",
        "title": "Modelos de Lenguaje Grande",
        "title_en": "Large Language Models (LLMs)",
        "category": "IA Generativa y Lenguaje",
        "difficulty": "Avanzado",
        "short_desc": "Modelos probabilísticos basados en redes neuronales masivas entrenadas con miles de millones de tokens para modelar la distribucion conjunta del texto.",
        "full_definition": "Un Modelo de Lenguaje Grande es una arquitectura autoregresiva o de enmascaramiento con miles de millones de parametros, parametrizada para aproximar la distribucion P(w_t | w_1, ..., w_{t-1}). Mediante aprendizaje autosupervisado sobre corpus textuales a escala web, el modelo adquiere capacidades emergentes como razonamiento en cadena, sintesis de codigo y comprension contextual profunda.",
        "real_world_example": "Generacion automatizada de borradores legales, conversion de consultas en lenguaje natural a consultas SQL y copilotos de programacion de software.",
        "technical_detail": "Prediccion de distribucion softmax sobre un vocabulario V: P(w_t = v) = exp(z_v) / sum_j exp(z_j), calculada a partir de los estados ocultos de la ultima capa del decodificador.",
        "historical_milestone": "En 2020, OpenAI publico GPT-3 con 175 mil millones de parametros, demostrando la capacidad de aprendizaje mediante pocos ejemplos (few-shot learning).",
        "image_name": "03_llm.jpg",
        "tags": "transformers, autoregresivo, lenguaje, embeddings, tokenizacion"
    },
    {
        "slug": "arquitectura-transformer",
        "title": "Arquitectura Transformer",
        "title_en": "Transformer Architecture",
        "category": "Arquitecturas y Modelos",
        "difficulty": "Avanzado",
        "short_desc": "Arquitectura de red neuronal basada exclusivamente en mecanismos de autoatencion, eliminando la recurrencia y permitiendo paralelismo masivo.",
        "full_definition": "El Transformer reemplazo a las redes neuronales recurrentes (RNN y LSTM) mediante el calculo directo de dependencias entre cualquier par de posiciones en una secuencia, independientemente de su distancia temporal. Esta compuesto por bloques de codificador y decodificador que incorporan autoatencion multicabezal (Multi-Head Attention), redes prealimentadas punto a punto y normalizacion de capas residuales.",
        "real_world_example": "Traduccion instantanea multilingue de documentos oficiales entre mas de 100 idiomas preservando matices gramaticales y contextuales complejos.",
        "technical_detail": "Atencion escalada producto punto: Attention(Q, K, V) = softmax((Q * K^T) / sqrt(d_k)) * V, calculada en h cabezales de atencion en paralelo.",
        "historical_milestone": "En junio de 2017, investigadores de Google publicaron el articulo seminal 'Attention Is All You Need', transformando permanentemente el campo de la IA moderna.",
        "image_name": "04_transformer.jpg",
        "tags": "self-attention, paralelismo, codificador, decodificador, nlp"
    },
    {
        "slug": "mecanismo-de-autoatencion",
        "title": "Mecanismo de Autoatención",
        "title_en": "Self-Attention Mechanism",
        "category": "Arquitecturas y Modelos",
        "difficulty": "Avanzado",
        "short_desc": "Operacion matematica que permite a una secuencia ponderar dinamicamente la relevancia relativa de cada uno de sus elementos respecto a los demas.",
        "full_definition": "La autoatencion proyecta cada vector de entrada en tres espacios lineales distintos: Consulta (Query), Clave (Key) y Valor (Value). Al multiplicar la consulta de una palabra por las claves de todas las demas en la oracion, genera una distribucion de probabilidades normalizada que determina cuanta importancia debe asignarse a cada posicion al sintetizar la representacion final.",
        "real_world_example": "Resolucion de anáforas en oraciones ambiguas: en 'El animal no cruzo la calle porque estaba muy cansado', el mecanismo asocia 'estaba cansado' con 'animal' en lugar de 'calle'.",
        "technical_detail": "Matriz de pesos de atencion A = softmax(Q * K^T / sqrt(d_k)), donde cada fila suma 1 y modula la agregacion de los vectores de valores V.",
        "historical_milestone": "Introducido formalmente por Bahdanau et al. (2014) como mecanismo de alineacion y refinado como autoatencion completa en la arquitectura Transformer en 2017.",
        "image_name": "05_self_attention.jpg",
        "tags": "matrices, query-key-value, proyeccion-lineal, pesos-atencion"
    },
    {
        "slug": "aprendizaje-supervisado",
        "title": "Aprendizaje Supervisado",
        "title_en": "Supervised Learning",
        "category": "Machine Learning Clásico",
        "difficulty": "Principiante",
        "short_desc": "Paradigma de entrenamiento donde el algoritmo aprende una funcion de mapeo a partir de pares ordenados de entrada y etiqueta objetivo conocida.",
        "full_definition": "En el aprendizaje supervisado, se dispone de un conjunto de datos formalizado como D = {(x_1, y_1), (x_2, y_2), ..., (x_n, y_n)}, donde x_i representa el vector de caracteristicas e y_i es la variable objetivo. El objetivo consiste en encontrar una funcion hipotetica f: X -> Y que minimice la discrepancia empirica entre las predicciones del modelo y las etiquetas verdaderas sobre datos no observados.",
        "real_world_example": "Deteccion de transacciones bancarias fraudulentas a partir de registros historicos etiquetados como 'legitima' o 'fraude confirmado'.",
        "technical_detail": "Optimizacion empirica del riesgo: min_theta (1/n) sum L(f(x_i; theta), y_i) + lambda * R(theta), donde L es la funcion de perdida (entropia cruzada o MSE) y R es el termino regularizador.",
        "historical_milestone": "El desarrollo de la Regresion Logistica por David Cox en 1958 y el algoritmo de Arboles de Decision ID3 por Ross Quinlan en 1986 consolidaron este paradigma.",
        "image_name": "06_aprendizaje_supervisado.jpg",
        "tags": "clasificacion, regresion, etiquetas, funcion-perdida, cross-validation"
    },
    {
        "slug": "aprendizaje-no-supervisado",
        "title": "Aprendizaje No Supervisado",
        "title_en": "Unsupervised Learning",
        "category": "Machine Learning Clásico",
        "difficulty": "Principiante",
        "short_desc": "Metodos que analizan y descubren estructuras subyacentes, distribuciones de probabilidad o agrupamientos en datos sin etiquetas previas.",
        "full_definition": "El aprendizaje no supervisado opera sobre conjuntos de datos {x_1, x_2, ..., x_n} sin supervision externa ni etiquetas asociadas. Sus objetivos principales abarcan la reduccion de dimensionalidad (proyeccion en subespacios de menor rango preservando varianza o topologia), la estimacion de densidad de probabilidad y el agrupamiento particional o jerarquico de muestras por similitud metrica.",
        "real_world_example": "Segmentacion automatica de clientes en plataformas de comercio electronico segun patrones de navegacion y volumen de gasto para personalizar campanas.",
        "technical_detail": "Algoritmo K-Means: minimizacion de la inercia sum_{j=1}^k sum_{x in S_j} ||x - mu_j||^2, o descomposicion espectral en PCA maximizando la varianza proyectada.",
        "historical_milestone": "Stuart Lloyd propuso en 1957 el algoritmo de cuantizacion vectorial que sento las bases del agrupamiento K-Means, publicado oficialmente en 1982.",
        "image_name": "07_aprendizaje_no_supervisado.jpg",
        "tags": "clustering, pca, k-means, manifold, dimensionalidad"
    },
    {
        "slug": "aprendizaje-por-refuerzo",
        "title": "Aprendizaje por Refuerzo",
        "title_en": "Reinforcement Learning (RL)",
        "category": "Optimización y Políticas",
        "difficulty": "Avanzado",
        "short_desc": "Marco de toma de decisiones secuenciales donde un agente aprende a maximizar una senal de recompensa acumulativa interactuando con un entorno dinamico.",
        "full_definition": "Modelado formalmente como un Proceso de Decision de Markov (MDP) definido por una tupla (S, A, P, R, gamma). El agente observa el estado actual s_t, ejecuta una accion a_t segun una politica pi(a|s), recibe una recompensa escalar r_t y transita al estado subsiguiente s_{t+1}. A traves del balance entre exploracion y explotacion, optimiza el retorno esperado descontado.",
        "real_world_example": "Control y optimizacion energetica de sistemas de refrigeracion en centros de datos a gran escala, reduciendo el consumo electrico hasta un 40%.",
        "technical_detail": "Ecuacion de Optimalidad de Bellman: Q*(s, a) = R(s, a) + gamma * sum_{s'} P(s'|s, a) * max_{a'} Q*(s', a').",
        "historical_milestone": "En 2016, AlphaGo de DeepMind derroto al campeon mundial Lee Sedol en el milenario juego de Go aplicando redes neuronales y busqueda Monte Carlo sobre politicas RL.",
        "image_name": "08_aprendizaje_refuerzo.jpg",
        "tags": "q-learning, bellman, agente, entorno, recompensa, alphago"
    },
    {
        "slug": "rlhf-alineacion-feedback-humano",
        "title": "RLHF (Refuerzo con Feedback Humano)",
        "title_en": "Reinforcement Learning from Human Feedback (RLHF)",
        "category": "Alineación de Modelos",
        "difficulty": "Avanzado",
        "short_desc": "Tecnica de entrenamiento que calibra las respuestas de un modelo de lenguaje con preferencias humanas utilizando un modelo de recompensa entrenado con comparaciones.",
        "full_definition": "RLHF es una metodologia de tres etapas: primero se realiza ajuste supervisado (SFT) sobre dialogos instructivos de alta calidad; segundo, se recopilan clasificaciones humanas de respuestas alternativas para entrenar un Modelo de Recompensa (Reward Model); finalmente, se optimiza la politica del modelo generativo mediante algoritmos como Proximal Policy Optimization (PPO) o Direct Preference Optimization (DPO).",
        "real_world_example": "Entrenamiento de asistentes conversacionales para rehusar peticiones maliciosas (fabricacion de malware) mientras responden con precision y empatia preguntas educativas.",
        "technical_detail": "Funcion objetivo PPO con penalizacion KL: max_theta E[R_phi(x, y) - beta * D_KL(pi_theta(y|x) || pi_ref(y|x))], impidiendo que el modelo se aleje demasiado de su distribucion base.",
        "historical_milestone": "Christiano et al. (2017) introdujeron la formulacion de RL desde comparaciones humanas, y en 2022 Ouyang et al. demostraron su eficacia a escala masiva en InstructGPT.",
        "image_name": "09_rlhf.jpg",
        "tags": "alineacion, ppo, dpo, reward-model, preferencias-humanas"
    },
    {
        "slug": "vision-por-computadora",
        "title": "Visión por Computadora",
        "title_en": "Computer Vision (CV)",
        "category": "Percepción y Sensores",
        "difficulty": "Intermedio",
        "short_desc": "Disciplina que capacita a los sistemas digitales para adquirir, procesar, analizar y comprender informacion visual multidimensional del mundo fisico.",
        "full_definition": "La vision artificial transforma matrices de pixeles en comprension semantica de alto nivel. Comprende tareas fundamentales como clasificacion de imagenes, localizacion de cuadros delimitadores (Object Detection), segmentacion semantica y panoptica pixel a pixel, y estimacion de pose tridimensional, utilizando arquitecturas convolucionales (CNN) y Vision Transformers (ViT).",
        "real_world_example": "Deteccion automatica de anomalias celulares en mamografias y tomografias computarizadas asistiendo a especialistas radiologos con precision submilimetrica.",
        "technical_detail": "Operacion de convolucion discreta 2D: S(i, j) = (I * K)(i, j) = sum_m sum_n I(i - m, j - n) * K(m, n), aplicando kernels espaciales con invariancia de traslacion.",
        "historical_milestone": "David Marr publico en 1982 su vision computacional tripartita (computacional, algoritmica e implementativa), sentando los principios modernos de la disciplina.",
        "image_name": "10_vision_computadora.jpg",
        "tags": "convolucion, segmentacion, pixeles, yolo, vit, deteccion"
    },
    {
        "slug": "procesamiento-lenguaje-natural",
        "title": "Procesamiento del Lenguaje Natural",
        "title_en": "Natural Language Processing (NLP)",
        "category": "Lenguaje y Semántica",
        "difficulty": "Intermedio",
        "short_desc": "Campo en la interseccion de la informatica y la linguistica enfocado en permitir la comunicacion coherente entre humanos y computadoras.",
        "full_definition": "El PLN abarca el modelado computacional del lenguaje humano en todos sus niveles formales: morfologico (lematizacion, segmentacion), sintactico (analisis de dependencias), semantico (significado y desambiguacion) y pragmatico (intencion y contexto comunicativo). Emplea representaciones vectoriales densas y modelos secuenciales para decodificar ambiguedades linguisticas.",
        "real_world_example": "Herramientas de filtrado inteligente de correo corporativo que identifican intentos de phishing detectando urgencia artificial y anomalias gramaticales sutiles.",
        "technical_detail": "Algoritmos de subpalabras como Byte-Pair Encoding (BPE) o WordPiece que mapean cadenas de caracteres crudas a indices de tokens en un vocabulario de tamano fijo.",
        "historical_milestone": "En 2013, Tomas Mikolov y su equipo en Google crearon Word2Vec, demostrando que las palabras pueden proyectarse en vectores con propiedades algebraicas semanticas.",
        "image_name": "11_nlp.jpg",
        "tags": "linguistica, semantica, tokenizacion, bpe, sintaxis, lematizacion"
    },
    {
        "slug": "modelos-de-difusion",
        "title": "Modelos de Difusión",
        "title_en": "Diffusion Models",
        "category": "IA Generativa y Lenguaje",
        "difficulty": "Avanzado",
        "short_desc": "Modelos generativos que sintetizan datos de alta fidelidad aprendiendo a revertir un proceso estocastico gradual de adicion de ruido gaussiano.",
        "full_definition": "Un modelo de difusion consta de dos procesos opuestos: un proceso directo (Forward Process) que degrada progresivamente los datos agregando ruido gaussiano segun un esquema predeterminado beta_1, ..., beta_T, y un proceso inverso (Reverse Process) parametrizado por una red neuronal (tipicamente U-Net) entrenada para predecir y restar el componente de ruido en cada paso temporal.",
        "real_world_example": "Generadores de arte digital de grado cinematografico y diseno asistido de nuevas moleculas proteicas para farmacos terapeuticos en biomedicina.",
        "technical_detail": "Objetivo simplificado de Ho et al. (DDPM): L_simple(theta) = E_{t, x_0, epsilon} [ ||epsilon - epsilon_theta(sqrt(alpha_bar_t) * x_0 + sqrt(1 - alpha_bar_t) * epsilon, t)||^2 ].",
        "historical_milestone": "Sohl-Dickstein et al. (2015) formularon los principios de termodinamica de no equilibrio, perfeccionados en 2020 por Ho et al. con los Denoising Diffusion Probabilistic Models (DDPM).",
        "image_name": "12_modelos_difusion.jpg",
        "tags": "ddpm, ruido-gaussiano, unet, imagen-sintetica, estocastico"
    },
    {
        "slug": "redes-generativas-antagonicas",
        "title": "Redes Generativas Antagónicas",
        "title_en": "Generative Adversarial Networks (GANs)",
        "category": "IA Generativa y Lenguaje",
        "difficulty": "Avanzado",
        "short_desc": "Arquitectura de aprendizaje rival compuesta por dos redes neuronales que compiten en un juego minimax de suma cero para generar datos hiperrealistas.",
        "full_definition": "Las GANs enfrentan simultaneamente a un Generador G, que transforma vectores de ruido latente z ~ p_z en muestras sinteticas G(z), contra un Discriminador D, que calcula la probabilidad de que una muestra provenga del conjunto de datos real o del generador. Durante la optimizacion, el discriminador mejora su capacidad forense mientras el generador perfecciona su capacidad de falsificacion verosimil.",
        "real_world_example": "Superresolucion fotografica y restauracion de peliculas cinematograficas historicas danadas o digitalizadas con baja tasa de muestreo.",
        "technical_detail": "Juego minimax con valor funcional V(D, G) = E_{x ~ p_data}[log D(x)] + E_{z ~ p_z}[log(1 - D(G(z)))]. El optimo teorico se alcanza cuando p_g = p_data (divergencia Jensen-Shannon minima).",
        "historical_milestone": "Ian Goodfellow y colaboradores concibieron y formalizaron la arquitectura GAN en una publicacion que conmociono a la comunidad cientifica en 2014.",
        "image_name": "13_gans.jpg",
        "tags": "minimax, generador, discriminador, juego-teoria, jensen-shannon"
    },
    {
        "slug": "generacion-aumentada-por-recuperacion",
        "title": "Generación Aumentada por Recuperación",
        "title_en": "Retrieval-Augmented Generation (RAG)",
        "category": "Arquitecturas y Modelos",
        "difficulty": "Intermedio",
        "short_desc": "Tecnica que mejora la precision de los modelos generativos consultando dinamica y fidedignamente fuentes documentales externas antes de emitir una respuesta.",
        "full_definition": "RAG desacopla el razonamiento del modelo de su memoria parametrica estatica. Cuando un usuario formula una consulta, el sistema convierte la pregunta en un vector denso, ejecuta una busqueda por similitud semantica (k-nearest neighbors) en una base de datos vectorial contra fragmentos documentales indexados y ensambla un prompt aumentado con la evidencia factual recuperada para alimentar al LLM.",
        "real_world_example": "Motores de busqueda interna para firmas contables y despachos de auditoria que responden citando normativas fiscales vigentes con referencias precisas de articulos.",
        "technical_detail": "Pipeline RAG estandar: recuperacion top-k chunks = argmax_{d in D} cos(e(q), e(d)), seguido de P(y | q, d_{1:k}) computado por el modelo generativo condicionado al contexto inyectado.",
        "historical_milestone": "Lewis et al. (Meta AI) publicaron en 2020 el articulo fundacional 'Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks'.",
        "image_name": "14_rag.jpg",
        "tags": "base-vectorial, embeddings, similitud-coseno, facticidad, prompt"
    },
    {
        "slug": "incrustaciones-vectoriales",
        "title": "Incrustaciones Vectoriales",
        "title_en": "Vector Embeddings",
        "category": "Representación Semántica",
        "difficulty": "Intermedio",
        "short_desc": "Mapeo de objetos del mundo real a vectores densos en un espacio de dimension continua donde la cercania geometrica refleja afinidad conceptual.",
        "full_definition": "Un embedding es una funcion continua f: S -> R^d que traslada entidades simbolicas discretas (palabras, frases, imagenes, audio, grafos) a vectores en un espacio euclidiano multidimensional (frecuentemente entre 384 y 3072 dimensiones). En este espacio, las operaciones geometricas reflejan relaciones semanticas: la similitud coseno entre dos vectores cuantifica su proximidad tematica.",
        "real_world_example": "Sistemas de recomendacion de musica en streaming que encuentran canciones similares basandose en la cercania geometrica de sus atributos acusticos incrustados.",
        "technical_detail": "Metrica de similitud coseno: cos(u, v) = (u . v) / (||u||_2 * ||v||_2), variando en el rango [-1, 1], invariante a la magnitud de los vectores normalizados.",
        "historical_milestone": "La hipotesis distribucional de J.R. Firth (1957) 'Conoceras a una palabra por la compania que frecuenta' dio origen a las representaciones vectoriales modernas.",
        "image_name": "15_embeddings.jpg",
        "tags": "espacio-latente, similitud-coseno, vectores-densos, semantica"
    },
    {
        "slug": "agentes-autonomos-de-ia",
        "title": "Agentes Autónomos y Multi-Agente",
        "title_en": "Autonomous AI Agents & Multi-Agent Systems",
        "category": "Agentes y Razonamiento",
        "difficulty": "Avanzado",
        "short_desc": "Entidades computacionales dirigidas por modelos fundacionales capaces de planificar, descomponer metas, invocar herramientas externas y autoevaluar su progreso.",
        "full_definition": "Un agente autonomo orquesta un bucle cognitivo continuo: analiza su entorno, formula un plan estrategico, ejecuta acciones a traves de interfaces de programacion (APIs, navegadores, terminales), almacena memorias intermedias (a corto y largo plazo) y reflexiona sobre los errores detectados para corregir su trayectoria sin intervencion humana directa.",
        "real_world_example": "Agentes de ciberseguridad que investigan de forma autonoma una alerta de intrusion, ejecutan pruebas forenses en servidores afectados y generan parches de mitigacion.",
        "technical_detail": "Framework de razonamiento ReAct (Reasoning + Acting): generacion intercalada de trazas de pensamiento ('Thought'), acciones de invocacion ('Act[tool(args)]') y observaciones ('Obs').",
        "historical_milestone": "El desarrollo del paradigma ReAct por Yao et al. (2022) y el experimento sociologico de agentes generativos en 'Smallville' por Park et al. (Stanford, 2023).",
        "image_name": "16_agentes_inteligentes.jpg",
        "tags": "react, herramientas, memoria, planificacion, ejecucion"
    },
    {
        "slug": "alucinacion-en-modelos-de-lenguaje",
        "title": "Alucinación en Modelos de Lenguaje",
        "title_en": "AI Hallucination",
        "category": "Seguridad y Confiabilidad",
        "difficulty": "Principiante",
        "short_desc": "Fenomeno donde un modelo genera contenido sintacticamente plausible y convincente pero facticamente falso, inventado o incoherente.",
        "full_definition": "Las alucinaciones son consecuencia directa de la naturaleza estocastica de los LLMs: los modelos predicen la continuacion probabilistica mas verosimil de una secuencia, no consultan una base ontologica de verdad. Se dividen en alucinaciones intrinsecas (contradicen la informacion aportada en el contexto de entrada) y extrinsecas (generan afirmaciones indemostrables con los datos disponibles).",
        "real_world_example": "Un modelo que redacta un memorial juridico citando con absoluta seguridad precedentes judiciales con numeros de caso, jueces y sentencias que nunca existieron.",
        "technical_detail": "Mitigacion mediante tecnicas de decodificacion restringida, calibracion de temperatura softmax (T cercana a 0), contraste factual mediante RAG y verificacion cruzada (Self-Consistency).",
        "historical_milestone": "Identificado como problema critico en la transicion de los sistemas basados en reglas a los modelos de lenguaje neuronales a partir de 2018 y extensamente documentado en 2023.",
        "image_name": "17_alucinacion.jpg",
        "tags": "seguridad, facticidad, calibracion, sesgo, veracidad, mitigacion"
    },
    {
        "slug": "ajuste-fino-y-lora",
        "title": "Ajuste Fino y LoRA",
        "title_en": "Fine-Tuning & Low-Rank Adaptation (LoRA)",
        "category": "Adaptación de Modelos",
        "difficulty": "Avanzado",
        "short_desc": "Metodologia que adapta un modelo preentrenado a un dominio o tarea especifica modificando o congelando pesos mediante matrices de bajo rango.",
        "full_definition": "El ajuste fino tradicional recalcula todos los pesos parametricos del modelo sobre un conjunto de datos especializado. En contraste, LoRA (Low-Rank Adaptation) congela los pesos preentrenados W_0 y descompone la matriz de actualizacion Delta W en dos matrices de rango intrinseco mucho menor: Delta W = B * A (donde B in R^{d x r}, A in R^{r x k}, con r << min(d, k)), reduciendo hasta en un 99% el consumo de memoria GPU.",
        "real_world_example": "Adaptacion de un modelo de lenguaje de proposito general para extraer con precision diagnosticos codificados segun el estandar medico CIE-11 a partir de notas clinicas.",
        "technical_detail": "Salida adaptada: h = W_0 * x + (alpha / r) * B * A * x, donde alpha es una constante de escalamiento hiperparametrica que controla la magnitud de la actualizacion aprendida.",
        "historical_milestone": "Edward Hu y coautores (Microsoft Research) introdujeron LoRA en 2021, democratizando el ajuste fino de modelos masivos en hardware de grado consumidor.",
        "image_name": "18_fine_tuning.jpg",
        "tags": "lora, peft, gpu, matrices-bajo-rango, pesos, adaptacion"
    },
    {
        "slug": "descenso-de-gradiente-y-retropropagacion",
        "title": "Descenso de Gradiente y Retropropagación",
        "title_en": "Gradient Descent & Backpropagation",
        "category": "Optimización Matemática",
        "difficulty": "Intermedio",
        "short_desc": "Algoritmo matematico fundamental que calcula derivadas parciales mediante la regla de la cadena para actualizar los pesos de una red minimizando el error.",
        "full_definition": "La retropropagacion (Backpropagation) calcula de forma eficiente el gradiente de la funcion de costo respecto a cada parametro de la red, propagando la senal de error hacia atras desde la salida hasta la entrada. El Descenso de Gradiente utiliza estos vectores direccionales para actualizar iterativamente los parametros en direccion opuesta a la maxima tasa de incremento de la perdida.",
        "real_world_example": "Ajuste milimetrico de los millones de coeficientes de un sistema de reconocimiento de voz durante cientos de epocas de entrenamiento para reducir el error fonetico.",
        "technical_detail": "Regla de actualizacion de pesos: theta_{t+1} = theta_t - eta * grad_theta J(theta_t), complementada con momentos en variantes modernas como Adam (estimacion adaptativa de momentos de primer y segundo orden).",
        "historical_milestone": "Popularizado de forma definitiva en 1986 por David Rumelhart, Geoffrey Hinton y Ronald Williams en la revista Nature, reactivando la investigacion conexionista.",
        "image_name": "19_descenso_gradiente.jpg",
        "tags": "calculo, derivadas, regla-de-la-cadena, adam, optimizacion"
    },
    {
        "slug": "sobreajuste-y-regularizacion",
        "title": "Sobreajuste y Regularización",
        "title_en": "Overfitting & Regularization",
        "category": "Validación y Métricas",
        "difficulty": "Principiante",
        "short_desc": "Dilema donde un modelo memoriza el ruido del conjunto de entrenamiento perdiendo capacidad de generalizar frente a muestras nuevas del mundo real.",
        "full_definition": "El sobreajuste (Overfitting) ocurre cuando la complejidad del modelo excede la informacion genuina disponible en los datos de entrenamiento, capturando correlaciones espurias. Las tecnicas de regularizacion imponen restricciones a la capacidad del modelo para inducir soluciones mas parsimoniosas: regularizacion L1 (Lasso) promueve escasez, L2 (Ridge) penaliza magnitudes elevadas, y Dropout desactiva neuronas aleatoriamente durante el entrenamiento.",
        "real_world_example": "Un modelo predictivo del mercado bursatil que predice a la perfeccion cotizaciones del pasado ano pero falla catastroficamente al predecir la semana siguiente.",
        "technical_detail": "Termino de regularizacion L2: J_reg(theta) = J(theta) + (lambda / 2) * ||theta||_2^2. Dropout: cada activacion h_i se multiplica por una variable bernoulli r_i ~ Bernoulli(p).",
        "historical_milestone": "Nitish Srivastava, Geoffrey Hinton y equipo presentaron el metodo Dropout en 2014, demostrando una reduccion drastica del sobreajuste en redes profundas.",
        "image_name": "20_sobreajuste.jpg",
        "tags": "bias-variance, dropout, lasso, ridge, generalizacion, perdida"
    }
]


def seed() -> None:
    """
    Inserta o actualiza los 20 conceptos clave en la base de datos SQLite.
    Garantiza idempotencia: si la base ya contiene datos, los actualiza sin duplicar.
    """
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    print(f"Iniciando siembra de {len(CONCEPTS_DATA)} conceptos tecnicos de IA...")

    for concept in CONCEPTS_DATA:
        cursor.execute(
            """
            INSERT INTO concepts (
                slug, title, title_en, category, difficulty,
                short_desc, full_definition, real_world_example,
                technical_detail, historical_milestone, image_name, tags
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
                title=excluded.title,
                title_en=excluded.title_en,
                category=excluded.category,
                difficulty=excluded.difficulty,
                short_desc=excluded.short_desc,
                full_definition=excluded.full_definition,
                real_world_example=excluded.real_world_example,
                technical_detail=excluded.technical_detail,
                historical_milestone=excluded.historical_milestone,
                image_name=excluded.image_name,
                tags=excluded.tags
            """,
            (
                concept["slug"],
                concept["title"],
                concept["title_en"],
                concept["category"],
                concept["difficulty"],
                concept["short_desc"],
                concept["full_definition"],
                concept["real_world_example"],
                concept["technical_detail"],
                concept["historical_milestone"],
                concept["image_name"],
                concept["tags"]
            )
        )

    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM concepts")
    total = cursor.fetchone()[0]
    conn.close()

    print(f"Siembra completada con exito. Total de conceptos registrados: {total}")


if __name__ == "__main__":
    seed()
