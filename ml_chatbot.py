"""
ml_chatbot.py
Motor de clasificacion y argumentacion contextual para el Chatbot de Algoritmos
de Busqueda impulsado por Machine Learning for Kids (ML for Kids).

Etiquetas soportadas (4 clases):
  - Heuristica
  - Ciega
  - Evolutiva
  - Desconocido

Caracteristicas principales:
  1. Funciona tanto SIN cuenta en ML for Kids (mediante el modelo local entrenable
     en vivo con las 4 cubetas de etiquetas, igual que el modo 'Probar sin registrarse'
     de ML for Kids) como CON cuenta en la nube (mediante API Key).
  2. Analizador Discursivo Multi-Mencion: clasifica correctamente incluso si se
     mencionan los 3 algoritmos en un mismo texto (con o sin comas, en preguntas,
     comparaciones o descartes).
  3. Argumentacion Contextual Dinamica: en lugar de repetir plantillas rigidas,
     analiza que algoritmo especifico (A*, Voraz, BFS, DFS, UCS, IDDFS, Geneticos,
     ACO, PSO), que escenario (GPS, laberinto, optimizacion) y que tipo de
     intencion (pregunta, caso practico, comparacion, saludo o trampa coloquial)
     planteo el usuario para redactar una respuesta natural y especifica.
"""

import os
import re
import json
import math
import unicodedata
import urllib.request
import urllib.parse
import urllib.error
from collections import Counter
from typing import Dict, List, Any, Optional, Tuple


DEFAULT_MLFORKIDS_API_KEY = os.environ.get("MLFORKIDS_API_KEY", "").strip()

LABELS = ("Heuristica", "Ciega", "Evolutiva", "Desconocido")
ALGORITHM_LABELS = ("Heuristica", "Ciega", "Evolutiva")


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower().strip()
    decomposed = unicodedata.normalize("NFD", text)
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    stripped = re.sub(r"\s+", " ", stripped)
    return stripped


def extract_mlforkids_key(raw_input: Optional[str]) -> str:
    """
    Extrae la API Key si el usuario pega la llave, la linea key = "..." o una URL
    de /api/scratch/<KEY>/classify. Si pega la URL del navegador en modo sin cuenta
    (#!/mlproject/localstorage/...), devuelve cadena vacia para indicar que es un
    proyecto de almacenamiento local del navegador.
    """
    if not raw_input:
        return DEFAULT_MLFORKIDS_API_KEY
    cleaned = raw_input.strip()
    if not cleaned:
        return DEFAULT_MLFORKIDS_API_KEY

    if "localstorage" in cleaned.lower() or "#!/mlproject" in cleaned.lower():
        return "__BROWSER_LOCALSTORAGE__"

    url_match = re.search(r"/api/scratch/([^/\s\"'?&]+)", cleaned)
    if url_match:
        return url_match.group(1).strip()

    py_match = re.search(r"key\s*=\s*['\"]([^'\"]+)['\"]", cleaned, flags=re.IGNORECASE)
    if py_match:
        return py_match.group(1).strip()

    return cleaned.strip("'\" ")


def canonicalize_label(raw_label: str) -> str:
    norm = normalize_text(raw_label).replace("_", " ").replace("-", " ")
    if "heurist" in norm or ("informad" in norm and "no informad" not in norm):
        return "Heuristica"
    if "cieg" in norm or "no informad" in norm:
        return "Ciega"
    if "evolut" in norm or "genet" in norm or "bioinspir" in norm:
        return "Evolutiva"
    return "Desconocido"


# ============================================================================
# CORPUS DE ENTRENAMIENTO (4 CUBETAS: Heuristica, Ciega, Evolutiva, Desconocido)
# ============================================================================
TRAINING_CORPUS: Dict[str, List[str]] = {
    "Heuristica": [
        "El algoritmo A* utiliza la funcion de evaluacion f(n) = g(n) + h(n) para encontrar la ruta optima.",
        "La busqueda heuristica o informada emplea conocimiento especifico del problema para guiar la exploracion.",
        "La funcion heuristica h(n) estima el costo restante desde el nodo actual hasta el estado meta.",
        "Para que A* sea optimo en arboles, la heuristica debe ser admisible, es decir, nunca sobreestimar el costo real.",
        "En grafos, A* garantiza optimalidad si la heuristica h(n) es consistente o monotona y cumple la desigualdad triangular.",
        "La busqueda voraz primero el mejor expande el nodo que parece estar mas cerca de la meta usando solo f(n) = h(n).",
        "IDA* combina la busqueda A* con profundizacion iterativa para reducir drasticamente el consumo de memoria.",
        "Los algoritmos RBFS y SMA* son variantes de busqueda informada disenadas para operar con memoria limitada.",
        "La distancia Manhattan y la distancia Euclidiana en linea recta son heuristicas clasicas para tableros y mapas GPS.",
        "En el calculo de ruta entre Puebla y Ciudad de Mexico, A* suma los kilometros recorridos g(n) mas la linea recta h(n).",
        "El pathfinding en videojuegos modernos utiliza A* ponderado para hallar caminos rapidos evitando obstaculos.",
        "Una heuristica informada permite podar ramas irrelevantes del espacio de estados y explorar menos nodos.",
        "Quiero guiar la busqueda hacia el objetivo utilizando una estimacion de distancia o costo futuro.",
        "Necesito resolver el puzzle del 8 usando el numero de fichas fuera de lugar o la distancia Manhattan como guia.",
        "Como funciona el algoritmo A estrella y que significa que su heuristica sea admisible y consistente.",
        "Busqueda informada con cola de prioridad ordenada por el valor estimado f(n) igual a g(n) mas h(n).",
        "A diferencia de la busqueda ciega y la evolutiva, este metodo guia la exploracion con una funcion heuristica h(n).",
        "No quiero explorar a ciegas ni usar mutaciones geneticas, prefiero estimar la distancia a la meta con A*.",
        "Descartando BFS y los algoritmos geneticos, elegimos busqueda voraz primero el mejor con heuristica admisible.",
        "Calculo de rutas optimas en navegacion vial mediante estimacion heuristica del costo restante hacia el destino."
    ],
    "Ciega": [
        "La busqueda ciega o no informada explora el espacio de estados sin ningun conocimiento sobre que tan cerca esta la meta.",
        "El algoritmo de busqueda en anchura BFS explora el arbol nivel por nivel utilizando una cola FIFO.",
        "La busqueda en profundidad DFS explora la rama actual hasta el fondo usando una pila LIFO o recursion.",
        "La busqueda de costo uniforme UCS expande siempre el nodo con el menor costo acumulado de ruta g(n).",
        "La busqueda en profundidad limitada DLS impone un limite maximo l para evitar perderse en ramas infinitas.",
        "La profundizacion iterativa IDDFS combina la completitud y optimalidad de BFS con el bajo consumo de memoria O(bm) de DFS.",
        "La busqueda bidireccional ejecuta dos busquedas simultaneas: una desde el estado inicial y otra hacia atras desde la meta.",
        "En un problema donde no existe funcion heuristica h(n) disponible, debemos explorar sistematicamente con busqueda no informada.",
        "BFS es completo y garantiza encontrar el camino mas corto cuando todos los costos de paso son iguales.",
        "La complejidad temporal y espacial de la busqueda en anchura es exponencial O(b elevado a la d).",
        "DFS puede quedar atrapado en ciclos o caminos infinitos si no se registra una lista cerrada de estados visitados.",
        "Quiero recorrer todos los nodos de un grafo pequeno sin usar heuristicas ni estimaciones de distancia.",
        "Como funciona el algoritmo BFS de busqueda en anchura y cual es la diferencia con DFS en profundidad.",
        "Exploracion exhaustiva y sistematica basada unicamente en la topologia formal del grafo y la definicion del problema.",
        "A diferencia de la busqueda heuristica con A* y de la busqueda evolutiva, la busqueda ciega no usa informacion del dominio.",
        "No tenemos funcion de aptitud fitness ni heuristica h(n), por lo que aplicamos busqueda de costo uniforme o BFS.",
        "En lugar de algoritmos geneticos o A estrella, resolvemos el laberinto explorando nivel por nivel con una cola FIFO.",
        "Busqueda no informada mediante expansion sistematica de la frontera en colas FIFO o pilas LIFO sin guia externa.",
        "Necesito encontrar una solucion garantizada en un arbol pequeno recorriendo por niveles sin funcion heuristica.",
        "El agente desconoce la direccion del objetivo y solo puede distinguir un estado meta cuando lo evalua con GoalTest."
    ],
    "Evolutiva": [
        "La busqueda evolutiva mantiene una poblacion de soluciones candidatas que evolucionan mediante seleccion natural.",
        "Los algoritmos geneticos aplican operadores de seleccion, cruce o recombinacion y mutacion sobre cromosomas.",
        "Cada individuo de la poblacion es evaluado mediante una funcion de aptitud o fitness que mide su calidad.",
        "A lo largo de generaciones sucesivas, los individuos mas aptos tienen mayor probabilidad de reproducirse.",
        "El operador de mutacion introduce variaciones aleatorias en los genes para mantener la diversidad genetica y evitar optimos locales.",
        "El operador de cruce o crossover combina el material genetico de dos padres para generar descendencia nueva.",
        "La programacion genetica, las estrategias evolutivas y la evolucion diferencial pertenecen al paradigma evolutivo.",
        "La inteligencia de enjambre incluye la optimizacion por enjambre de particulas PSO y la colonia de hormigas ACO.",
        "Los algoritmos bioinspirados exploran multiples regiones del espacio de busqueda en paralelo sin guardar el camino.",
        "Se utiliza para diseno industrial, optimizacion estructural, neuroevolucion y ajuste de hiperparametros complejos.",
        "No garantiza formalmente la solucion optima exacta, pero encuentra soluciones aproximadas de alta calidad en espacios enormes.",
        "Como funcionan los algoritmos geneticos y que papel juegan la seleccion por ruleta o torneo, el cruce y la mutacion.",
        "Quiero optimizar una funcion compleja evolucionando una poblacion de individuos con funcion de aptitud fitness.",
        "La colonia de hormigas ACO utiliza rastros de feromonas artificiales para descubrir rutas eficientes en grafos.",
        "El enjambre de particulas PSO ajusta la posicion y velocidad de cada agente segun su mejor experiencia personal y global.",
        "A diferencia de la busqueda ciega como BFS y de la heuristica A*, la busqueda evolutiva evoluciona poblaciones con genetica.",
        "Cuando la busqueda ciega es intratable y no queremos usar A*, empleamos algoritmos geneticos con cruce y mutacion.",
        "Descartando la exploracion sistematica de arboles con BFS o A*, optamos por seleccion natural y evolucion poblacional.",
        "Metaheuristica poblacional inspirada en la evolucion biologica de Darwin para problemas de optimizacion combinatoria.",
        "Generacion de soluciones mediante cromosomas binarios, evaluacion de fitness y reemplazo generacional con elitismo."
    ],
    "Desconocido": [
        "Hola buenos dias, como estas hoy y que puedes hacer por mi.",
        "Cual es la receta para preparar una pizza casera con masa italiana y salsa de tomate.",
        "Quien gano el partido de futbol de la liga de campeones ayer por la noche.",
        "Cual es el pronostico del clima y la temperatura para manana en la ciudad.",
        "Como se configura una base de datos relacional en PostgreSQL con llaves foraneas y triggers.",
        "Explicame que es la revolucion francesa y en que ano ocurrio la toma de la Bastilla.",
        "Necesito centrar un contenedor div en CSS utilizando flexbox y grid layout.",
        "Cuales son los mejores ejercicios de cardio para bajar de peso en el gimnasio.",
        "Me puedes recomendar una pelicula de ciencia ficcion o una serie de comedia en streaming.",
        "Cuanto cuesta el dolar hoy frente al peso mexicano en el banco.",
        "Como funciona el motor de combustion interna de un automovil hibrido.",
        "Cual es la capital de Australia y cuantos habitantes tiene actualmente.",
        "Escribe un poema corto sobre la naturaleza, las montanas y el oceano.",
        "Como instalar paquetes de Node.js con npm en Windows 11.",
        "Que es el calentamiento global y como afecta el derretimiento de los polos.",
        "Cual es la diferencia entre memoria RAM DDR4 y almacenamiento en disco solido SSD NVMe.",
        "Ayer fui al cine a ver una pelicula llamada evolucion a ciegas con mis amigos.",
        "Donde puedo comprar boletos de avion baratos para viajar en vacaciones de verano.",
        "Explicame como declarar impuestos mensuales en el portal de hacienda.",
        "Gracias por la informacion, hasta luego y que tengas una excelente tarde."
    ]
}


BLIND_ABSENCE_OF_HEURISTIC_REGEX = re.compile(
    r"\b(?:sin\s+(?:ningun\s+|ninguna\s+|usar\s+|emplear\s+|utilizar\s+|tener\s+|contar\s+con\s+)?|"
    r"no\s+(?:usa|usan|utiliza|utilizan|emplea|emplean|tiene|tienen|cuenta\s+con|requiere|dispone\s+de)\s+(?:ningun\s+|ninguna\s+)?|"
    r"(?:carece|ausencia|falta)\s+de\s+)"
    r"(?:conocimiento|informacion|funcion\s+heuristica|heuristica|heuristicas|estimacion|guia)"
    r"(?:\s+heuristic[ao]s?|\s+adicional(?:es)?|\s+del\s+problema|\s+del\s+dominio|\s+h\s*\(\s*n\s*\))?\b"
)


DOMAIN_PATTERNS: Dict[str, List[Tuple[str, float, str]]] = {
    "Heuristica": [
        (r"\bbusqueda\s+heuristic[ao]s?\b", 4.5, "Busqueda Heuristica"),
        (r"\bbusqueda\s+informad[ao]s?\b", 4.5, "Busqueda Informada"),
        (r"\bfuncion\s+heuristic[ao]\b", 4.2, "funcion heuristica"),
        (r"\bheuristic[ao]s?\s+admisibles?\b", 4.5, "heuristica admisible"),
        (r"\bheuristic[ao]s?\s+consistentes?\b", 4.5, "heuristica consistente"),
        (r"\bheuristic[ao]s?\b", 2.8, "estimacion heuristica"),
        (r"(?:^|\s|['\"(\[])a\*(?=$|\s|[.,;:?!)'\"\]])", 4.6, "algoritmo A*"),
        (r"\balgoritmo\s+a\s+estrella\b|\ba\s+estrella\b", 4.5, "algoritmo A estrella (A*)"),
        (r"\bida\*", 4.5, "algoritmo IDA*"),
        (r"\bsma\*", 4.5, "algoritmo SMA*"),
        (r"\brbfs\b", 4.4, "algoritmo RBFS"),
        (r"\bbusqueda\s+voraz\b", 4.2, "Busqueda Voraz"),
        (r"\bprimero\s+el\s+mejor\b|\bgreedy\s+best[\s-]first\b", 4.2, "estrategia Primero el Mejor"),
        (r"\bf\s*\(\s*n\s*\)\s*=\s*g\s*\(\s*n\s*\)\s*\+\s*h\s*\(\s*n\s*\)", 5.0, "formula f(n) = g(n) + h(n)"),
        (r"\bh\s*\(\s*n\s*\)", 3.8, "funcion h(n)"),
        (r"\bf\s*\(\s*n\s*\)", 2.8, "evaluacion f(n)"),
        (r"\bdistancia\s+manhattan\b", 3.8, "distancia Manhattan"),
        (r"\bdistancia\s+euclidian[ao]\b|\blinea\s+recta\b", 3.6, "distancia en linea recta (Euclidiana)"),
        (r"\bestima(?:r|cion|ndo)?\s+(?:la\s+|el\s+)?(?:distancia|costo|cercania)\b", 3.4, "estimacion de distancia hacia la meta"),
        (r"\badmisibilidad\b|\badmisible\b", 3.2, "propiedad de admisibilidad"),
        (r"\bpathfinding\b|\bruta\s+mas\s+corta\s+en\s+un\s+mapa\s+gps\b|\bmapa\s+gps\b", 3.0, "calculo de rutas en mapas/GPS"),
    ],
    "Ciega": [
        (r"\bbusqueda\s+cieg[ao]s?\b", 4.5, "Busqueda Ciega"),
        (r"\bbusqueda\s+no\s+informad[ao]s?\b", 4.5, "Busqueda No Informada"),
        (r"\bbusqueda\s+en\s+anchura\b|\bbusqueda\s+en\s+amplitud\b", 4.5, "Busqueda en Anchura (BFS)"),
        (r"\bbusqueda\s+en\s+profundidad\b", 4.5, "Busqueda en Profundidad (DFS)"),
        (r"\bcosto\s+uniforme\b", 4.5, "Busqueda de Costo Uniforme (UCS)"),
        (r"\bprofundidad\s+limitada\b", 4.4, "Profundidad Limitada (DLS)"),
        (r"\bprofundizacion\s+iterativa\b", 4.5, "Profundizacion Iterativa (IDDFS)"),
        (r"\bbusqueda\s+bidireccional\b", 4.4, "Busqueda Bidireccional"),
        (r"\bbfs\b", 4.3, "algoritmo BFS"),
        (r"\bdfs\b", 4.3, "algoritmo DFS"),
        (r"\bucs\b", 4.2, "algoritmo UCS"),
        (r"\bdls\b", 4.1, "algoritmo DLS"),
        (r"\biddfs\b", 4.4, "algoritmo IDDFS"),
        (r"\bcola\s+fifo\b|\bfifo\b", 3.5, "cola FIFO"),
        (r"\bpila\s+lifo\b|\blifo\b", 3.5, "pila LIFO"),
        (r"\bnivel\s+por\s+nivel\b|\bpor\s+niveles\b", 3.4, "exploracion nivel por nivel"),
        (r"\ba\s+ciegas\b", 2.6, "exploracion a ciegas"),
        (r"\bo\s*\(\s*b\s*\^\s*d\s*\)|\bo\s*\(\s*b\s*m\s*\)", 3.2, "complejidad O(b^d) u O(bm)"),
    ],
    "Evolutiva": [
        (r"\bbusqueda\s+evolutiv[ao]s?\b", 4.5, "Busqueda Evolutiva"),
        (r"\balgoritmos?\s+genetic[ao]s?\b", 4.6, "Algoritmos Geneticos"),
        (r"\bcomputacion\s+evolutiva\b", 4.5, "Computacion Evolutiva"),
        (r"\bestrategias?\s+evolutiv[ao]s?\b", 4.4, "Estrategias Evolutivas"),
        (r"\bprogramacion\s+genetica\b", 4.4, "Programacion Genetica"),
        (r"\bevolucion\s+diferencial\b", 4.4, "Evolucion Diferencial"),
        (r"\binteligencia\s+de\s+enjambre\b", 4.3, "Inteligencia de Enjambre"),
        (r"\benjambre\s+de\s+particulas\b|\bpso\b", 4.4, "Enjambre de Particulas (PSO)"),
        (r"\bcolonia\s+de\s+hormigas\b|\baco\b", 4.4, "Colonia de Hormigas (ACO)"),
        (r"\bseleccion\s+natural\b", 4.0, "seleccion natural"),
        (r"\bfuncion\s+de\s+aptitud\b|\bfitness\b", 4.2, "funcion de aptitud (fitness)"),
        (r"\bcruce\b|\bcrossover\b|\brecombinacion\b", 3.8, "operador de cruce / recombinacion"),
        (r"\bmutacion(?:es)?\b|\bmutan?\b", 3.9, "operador de mutacion"),
        (r"\bcromosomas?\b|\bgenes\b|\bgenotipo\b", 3.8, "representacion por cromosomas/genes"),
        (r"\bpoblacion\s+de\s+(?:soluciones|individuos|candidatos)\b|\bpoblaciones\b", 4.2, "poblacion de soluciones candidatas"),
        (r"\bgeneraciones\s+sucesivas\b|\breemplazo\s+generacional\b", 3.6, "evolucion por generaciones"),
        (r"\bbioinspirad[ao]s?\b|\bdarwin\b|\bferomonas?\b", 3.5, "inspiracion biologica"),
        (r"\bevolutiv[ao]s?\b", 2.8, "enfoque evolutivo"),
    ]
}

COLLOQUIAL_TRICK_PATTERNS = [
    r"\bpelicula\b", r"\bcine\b", r"\breceta\b", r"\bpizza\b", r"\bcocina\b",
    r"\bfutbol\b", r"\bpartido\b", r"\bclima\b", r"\bimpuestos\b", r"\bvacaciones\b"
]

NEGATION_AND_EXCLUSION_PATTERNS = [
    r"\ba\s+diferencia\s+de\b",
    r"\ben\s+lugar\s+de\b",
    r"\ben\s+vez\s+de\b",
    r"\blejos\s+de\b",
    r"\bpor\s+encima\s+de\b",
    r"\bantes\s+que\s+(?:la|el|los|las|usar|emplear|busqueda|algoritmo)\b",
    r"\bfrente\s+a\s+(?:la|el|los|las|busqueda|algoritmo)\b",
    r"\ben\s+comparacion\s+con\b",
    r"\bcomparad[oa]s?\s+con\b",
    r"\bsobre\s+(?:la\s+busqueda|el\s+algoritmo|los\s+algoritmos)\b",
    r"^\s*que\s+(?:la\s+|el\s+|los\s+|las\s+|usar\s+|emplear\s+)?(?:busqueda|algoritmo|bfs|dfs|a\*|genetico)",
    r"\bsin\s+(?:usar|emplear|utilizar|aplicar|recurrir|contar)\b",
    r"\b(?:excepto|salvo)\s+(?:la|el|los|las|en)\b",
    r"\bdescartando\b",
    r"\bdescartamos\b",
    r"\bdejando\s+(?:de\s+lado|atras)\b",
    r"\bolvidando\b",
    r"\bno\s+(?:quiero|queremos|usaremos|implementaremos|aplicaremos|emplearemos|elegimos|optamos|busco|prefiero|preferimos|necesito|necesitamos|usamos|uso|utilizamos|empleamos|aplicamos)\b",
    r"\bno\s+(?:usa|utiliza|emplea|aplica|es|son|funciona|funcionan|sirve|sirven)\s+(?:la\s+|el\s+|los\s+|las\s+|con\s+|para\s+)?(?:busqueda|algoritmos?|metodo|bfs|dfs|ucs|dls|iddfs|a\*|voraz|genetic[ao]s?|evolutiv[ao]s?|cieg[ao]s?|heuristic[ao]s?)\b",
    r"\btampoco\b",
    r"(?:^|\s)ni\s+(?:la\s+|el\s+|los\s+|las\s+|usar\s+|emplear\s+|tampoco\s+|con\s+|poblaciones\s+|mutacion\s+|funcion\s+|heuristica\s+|busqueda\s+|algoritmos?\s+|bfs\b|dfs\b|a\*)",
    r"\bcuando\s+la\s+busqueda\b.*\b(?:falla|no\s+basta|es\s+lenta|es\s+intratable|consume|se\s+vuelve)\b",
]

CONCESSIVE_START_PATTERNS = [
    r"^\s*(?:aunque|si\s+bien|pese\s+a\s+que|a\s+pesar\s+de\s+que|mientras\s+que|cuando\s+la|cuando\s+el|primero\s+pense|al\s+principio)\b"
]

CONTEXT_ENUM_PATTERNS = [
    r"^\s*(?:entre\s+la|entre\s+los|entre\s+busqueda|de\s+los\s+tres|de\s+las\s+tres|en\s+clase\s+vimos|existen\s+tres|comparando\s+la|hablando\s+de|tanto\s+la)\b"
]

FOCAL_INTENT_PATTERNS = [
    r"\b(?:necesito|necesitamos|quiero|queremos|busco|prefiero|preferimos|optamos\s+por|elegimos|elegi|decidi|usaremos|usamos|utilizamos|empleamos|implementaremos|aplicaremos|emplearemos|seleccionamos)\b",
    r"\b(?:explicame|dime|cual\s+es|como\s+funciona|que\s+algoritmo|cual\s+de\s+ellos|cual\s+de\s+las|cual\s+mantiene|cual\s+usa|cual\s+utiliza|cual\s+no\s+utiliza|cual\s+no\s+usa|cual\s+explora|me\s+interesa|hablame\s+de)\b",
    r"\b(?:por\s+lo\s+tanto|en\s+consecuencia|por\s+eso|asi\s+que|por\s+consiguiente|por\s+ende|finalmente|al\s+final|en\s+este\s+caso|para\s+este\s+problema|el\s+algoritmo\s+principal|la\s+solucion\s+es)\b",
    r"\b(?:unicamente|solamente|exclusivamente|se\s+resuelve\s+con|trata\s+de|es\s+mejor|es\s+mas\s+[a-z]+|resulta\s+mejor)\b",
    r"^\s*(?:pero|sin\s+embargo|no\s+obstante|en\s+cambio|mas\s+bien|sino\s+que|sino|por\s+el\s+contrario)\b",
]


class LocalMLForKidsClassifier:
    """
    Clasificador local entrenable en vivo con las 4 cubetas de ML for Kids
    (Heuristica, Ciega, Evolutiva, Desconocido). Funciona exactamente igual
    que el modo sin cuenta ('Probar sin registrarse') de ML for Kids.
    """

    def __init__(self, corpus: Dict[str, List[str]]) -> None:
        self.corpus = corpus
        self.class_doc_counts: Dict[str, int] = {}
        self.class_token_counts: Dict[str, Counter] = {}
        self.class_total_tokens: Dict[str, int] = {}
        self.vocab: set = set()
        self.total_docs = 0
        self.retrain()

    @staticmethod
    def extract_ngrams(text: str) -> List[str]:
        norm = normalize_text(text)
        raw_tokens = re.findall(r"[a-z0-9]+\*|[a-z]\([a-z0-9]+\)|[a-z0-9]+", norm)
        stopwords = {
            "de", "la", "el", "en", "y", "a", "los", "las", "un", "una", "para",
            "con", "por", "del", "al", "se", "es", "son", "que", "como", "su",
            "sus", "mas", "o", "u", "este", "esta", "estos", "estas", "lo", "le"
        }
        tokens = [t for t in raw_tokens if (t not in stopwords and len(t) > 1) or t in {"a*", "h(n)", "g(n)", "f(n)"}]
        bigrams = [f"{tokens[i]}_{tokens[i + 1]}" for i in range(len(tokens) - 1)]
        return tokens + bigrams

    def retrain(self) -> None:
        self.class_doc_counts.clear()
        self.class_token_counts.clear()
        self.class_total_tokens.clear()
        self.vocab.clear()
        self.total_docs = 0

        for label, texts in self.corpus.items():
            self.class_doc_counts[label] = len(texts)
            self.total_docs += len(texts)
            token_counter: Counter = Counter()
            for doc in texts:
                ngrams = self.extract_ngrams(doc)
                token_counter.update(ngrams)
                self.vocab.update(ngrams)
            self.class_token_counts[label] = token_counter
            self.class_total_tokens[label] = sum(token_counter.values())

    def add_example(self, label: str, example_text: str) -> bool:
        canon = canonicalize_label(label)
        clean_ex = (example_text or "").strip()
        if not clean_ex or canon not in self.corpus:
            return False
        if clean_ex not in self.corpus[canon]:
            self.corpus[canon].append(clean_ex)
            self.retrain()
        return True

    def score_text_fragment(self, text: str) -> Tuple[Dict[str, float], Dict[str, List[str]]]:
        norm = normalize_text(text)
        ngrams = self.extract_ngrams(text)
        vocab_size = max(1, len(self.vocab))

        log_scores: Dict[str, float] = {}
        for label in LABELS:
            prior = math.log(self.class_doc_counts[label] / max(1, self.total_docs))
            total_cls_tokens = self.class_total_tokens[label]
            cls_counts = self.class_token_counts[label]
            ll = prior
            for ng in ngrams:
                count = cls_counts.get(ng, 0)
                ll += math.log((count + 0.5) / (total_cls_tokens + 0.5 * vocab_size))
            log_scores[label] = ll

        max_nb = max(log_scores.values())
        nb_scaled = {lbl: (log_scores[lbl] - max_nb) * 0.42 for lbl in LABELS}

        domain_scores: Dict[str, float] = {lbl: 0.0 for lbl in LABELS}
        evidences: Dict[str, List[str]] = {lbl: [] for lbl in LABELS}

        first_person_reject = re.search(r"\bno\s+(?:quiero|queremos|prefiero|necesito|usaremos)\b", norm)
        norm_for_heuristica = norm
        if BLIND_ABSENCE_OF_HEURISTIC_REGEX.search(norm) and not first_person_reject:
            domain_scores["Ciega"] += 4.6
            evidences["Ciega"].append("exploracion sin informacion heuristica ni conocimiento adicional del problema")
            norm_for_heuristica = BLIND_ABSENCE_OF_HEURISTIC_REGEX.sub(" ", norm)

        for algo_label, pattern_list in DOMAIN_PATTERNS.items():
            target_norm = norm_for_heuristica if algo_label == "Heuristica" else norm
            for regex_pat, weight, description in pattern_list:
                if re.search(regex_pat, target_norm):
                    domain_scores[algo_label] += weight
                    if description not in evidences[algo_label]:
                        evidences[algo_label].append(description)

        colloquial_hits = sum(1 for pat in COLLOQUIAL_TRICK_PATTERNS if re.search(pat, norm))
        total_algo_score = sum(domain_scores[lbl] for lbl in ALGORITHM_LABELS)

        if total_algo_score < 2.2:
            domain_scores["Desconocido"] += 5.2
        elif colloquial_hits >= 2 and total_algo_score < 4.5:
            domain_scores["Desconocido"] += 6.0

        combined_logits: Dict[str, float] = {}
        for lbl in LABELS:
            combined_logits[lbl] = nb_scaled[lbl] + domain_scores[lbl]

        max_logit = max(combined_logits.values())
        exp_scores = {lbl: math.exp(combined_logits[lbl] - max_logit) for lbl in LABELS}
        sum_exp = sum(exp_scores.values())
        probs = {lbl: (exp_scores[lbl] / sum_exp) for lbl in LABELS}

        return probs, evidences


LOCAL_CLASSIFIER = LocalMLForKidsClassifier(TRAINING_CORPUS)


def check_mlforkids_status(raw_key: str, timeout: float = 4.5) -> Dict[str, Any]:
    clean_key = extract_mlforkids_key(raw_key)
    if clean_key == "__BROWSER_LOCALSTORAGE__":
        return {
            "connected": False,
            "key": "",
            "message": (
                "Pegaste la URL del navegador de un proyecto 'Sin cuenta' (localstorage). "
                "En ML for Kids sin cuenta, el modelo vive solo dentro de la pestaña de ese sitio y no genera API externa. "
                "Por ello, tienes activo aqui mismo el Modelo ML for Kids Integrado con las 4 cubetas (puedes agregarle mas ejemplos abajo si lo deseas)."
            )
        }

    if not clean_key:
        return {
            "connected": False,
            "key": "",
            "message": "Modo sin cuenta activo: el chatbot opera con el modelo entrenado integrado de 4 etiquetas."
        }

    status_url = f"https://machinelearningforkids.co.uk/api/scratch/{clean_key}/status"
    req = urllib.request.Request(
        status_url,
        headers={
            "User-Agent": "CompendioIA-MLForKids-Chatbot/1.0",
            "Accept": "application/json"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                status_code = data.get("status", 0)
                status_msg = data.get("msg", "Disponible")
                if status_code == 2:
                    return {
                        "connected": True,
                        "key": clean_key,
                        "message": f"Conectado exitosamente al modelo en la nube de Machine Learning for Kids ({status_msg})."
                    }
                return {
                    "connected": False,
                    "key": clean_key,
                    "message": f"El proyecto en ML for Kids reporta estado: {status_msg} (status={status_code})."
                }
    except Exception:
        pass

    test_preds = query_mlforkids_api(clean_key, "algoritmo de busqueda A* con funcion heuristica", timeout=timeout)
    if test_preds:
        return {
            "connected": True,
            "key": clean_key,
            "message": "Conectado exitosamente al endpoint de clasificacion de Machine Learning for Kids."
        }

    return {
        "connected": False,
        "key": "",
        "message": (
            "Esa llave o enlace no corresponde a un endpoint de nube activo en machinelearningforkids.co.uk "
            "(recuerda que el modo 'Probar sin registrarse' de ML for Kids no crea API en la nube). "
            "Se mantiene activo el Modelo ML for Kids Integrado con las 4 etiquetas."
        )
    }


def query_mlforkids_api(raw_key: str, text: str, timeout: float = 4.5) -> Optional[List[Dict[str, Any]]]:
    clean_key = extract_mlforkids_key(raw_key)
    if not clean_key or clean_key == "__BROWSER_LOCALSTORAGE__" or not text.strip():
        return None

    norm_check = normalize_text(text)
    query_str = text.strip()
    if BLIND_ABSENCE_OF_HEURISTIC_REGEX.search(norm_check) and not re.search(r"\bno\s+(?:quiero|prefiero|necesito)\b", norm_check):
        query_str = BLIND_ABSENCE_OF_HEURISTIC_REGEX.sub("busqueda ciega no informada sin guia", query_str)

    encoded_text = urllib.parse.quote(query_str[:500])
    url = f"https://machinelearningforkids.co.uk/api/scratch/{clean_key}/classify?data={encoded_text}"

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "CompendioIA-MLForKids-Chatbot/1.0",
            "Accept": "application/json"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status != 200:
                return None
            payload = json.loads(response.read().decode("utf-8"))
            if isinstance(payload, list) and len(payload) > 0:
                normalized_list = []
                for item in payload:
                    raw_cls = item.get("class_name", "")
                    conf = float(item.get("confidence", 0.0))
                    normalized_list.append({
                        "class_name": canonicalize_label(raw_cls),
                        "raw_class_name": raw_cls,
                        "confidence": conf
                    })
                return normalized_list
    except Exception:
        return None
    return None


def split_into_discourse_clauses(text: str) -> List[str]:
    working = text.strip()
    if not working:
        return []

    working = re.sub(
        r"\b((?:es\s+|son\s+|resulta\s+)?(?:mejor(?:es)?|mas\s+[a-záéíóúñ]+|preferible|superior(?:es)?))\s+"
        r"(que\s+(?:la|el|los|las|usar|emplear|busqueda|algoritmo|bfs|dfs|a\*))",
        r"\1 ||| \2",
        working,
        flags=re.IGNORECASE
    )

    pattern = (
        r"(?:\s*\|\|\|\s*)|"
        r"(?:[.;:?!]+)|"
        r"(?:,\s*(?=(?:pero|sin embargo|no obstante|en cambio|por el contrario|mas bien|sino|"
        r"mientras que|aunque|si bien|por lo tanto|por eso|asi que|en consecuencia|por consiguiente|"
        r"finalmente|al final|yo |nosotros |aqui |en este |prefiero|preferimos|necesito|necesitamos|quiero|queremos|"
        r"usamos|utilizamos|empleamos|aplicamos|implementaremos|optamos|elegimos|donde|cual|como|explicame|dime)\b))|"
        r"(?:\s+(?=(?:pero|sin embargo|no obstante|en cambio|por el contrario|mas bien|sino\s+que|sino\s+la|sino\s+el|sino\s+busqueda|"
        r"mientras que|aunque|si bien|por lo tanto|por eso|asi que|en consecuencia|por consiguiente|"
        r"a diferencia de|en lugar de|en vez de|lejos de|por encima de|antes que la|antes que el|antes que usar|"
        r"frente a la|frente al|en comparacion con|comparado con|comparada con|sobre la busqueda|excepto la|salvo la|"
        r"descartando|dejando de lado|sin usar|sin emplear|sin utilizar|sin recurrir|"
        r"ni tampoco|ni usar|ni emplear|ni la busqueda|ni el algoritmo|ni los algoritmos|ni poblaciones)\b))"
    )
    raw_parts = re.split(pattern, working, flags=re.IGNORECASE)
    clauses: List[str] = []

    contrast_start_re = re.compile(
        r"^\s*(?:a\s+diferencia\s+de|en\s+lugar\s+de|en\s+vez\s+de|aunque|si\s+bien|pese\s+a\s+que|"
        r"a\s+pesar\s+de\s+que|mientras\s+que|descartando|dejando\s+de\s+lado|sin\s+usar|sin\s+emplear|"
        r"no\s+quiero|no\s+queremos|no\s+necesito)\b",
        flags=re.IGNORECASE
    )
    focal_transition_re = re.compile(
        r"\s+(?=(?:yo\s+|nosotros\s+|aqui\s+|en\s+este\s+caso\s+|este\s+metodo\s+|este\s+algoritmo\s+)?"
        r"(?:usamos|utilizamos|empleamos|aplicamos|implementaremos|elegimos|optamos|prefiero|preferimos|"
        r"necesito|necesitamos|quiero|queremos|busco|buscamos|seleccionamos|me\s+interesa|explicame|dime)\b)",
        flags=re.IGNORECASE
    )

    for part in raw_parts:
        if not part or not part.strip():
            continue
        cleaned = part.strip(" ,")
        if not cleaned:
            continue

        sub_norm = normalize_text(cleaned)
        if contrast_start_re.search(sub_norm):
            sub_splits = focal_transition_re.split(cleaned, maxsplit=1)
            if len(sub_splits) == 2 and sub_splits[0].strip() and sub_splits[1].strip():
                clauses.append(sub_splits[0].strip(" ,"))
                clauses.append(sub_splits[1].strip(" ,"))
                continue

        is_enum_intro = any(re.search(p, sub_norm) for p in CONTEXT_ENUM_PATTERNS)
        algo_hits = sum(
            1 for lbl in ALGORITHM_LABELS
            if any(re.search(pat, sub_norm) for pat, _, _ in DOMAIN_PATTERNS[lbl])
        )
        if algo_hits >= 2 and "," in cleaned and not is_enum_intro:
            comma_parts = [p.strip() for p in cleaned.split(",") if p.strip()]
            if len(comma_parts) > 1:
                clauses.extend(comma_parts)
                continue
        clauses.append(cleaned)

    return clauses if clauses else [text.strip()]


def analyze_clause_discourse_role(
    clause: str,
    index: int,
    total_clauses: int,
    all_clauses_norm: List[str]
) -> Tuple[str, float, str]:
    norm = normalize_text(clause)

    is_interrogative_start = bool(
        re.search(r"^\s*[¿?]?\s*(?:cual|cuales|que\s+algoritmo|que\s+busqueda|que\s+metodo|como\s+funciona|por\s+que)\b", norm)
    )
    if is_interrogative_start and total_clauses > 1:
        return (
            "foco_principal",
            2.50,
            "contiene la pregunta central que define lo que realmente deseas saber"
        )

    for pat in NEGATION_AND_EXCLUSION_PATTERNS:
        if re.search(pat, norm):
            return (
                "contraste_o_negacion",
                0.06,
                "se menciona unicamente para descartarlo, negarlo o contrastarlo"
            )

    for pat in CONCESSIVE_START_PATTERNS:
        if re.search(pat, norm):
            return (
                "contraste_o_negacion",
                0.12,
                "se plantea como una condicion concesiva o secundaria ('aunque / mientras que')"
            )

    if index > 0:
        prev_norm = all_clauses_norm[index - 1]
        has_own_focal = any(re.search(p, norm) for p in FOCAL_INTENT_PATTERNS)
        if (norm.startswith("y ") or norm.startswith("o ")) and not has_own_focal:
            if any(re.search(p, prev_norm) for p in CONCESSIVE_START_PATTERNS + NEGATION_AND_EXCLUSION_PATTERNS):
                return (
                    "contraste_o_negacion",
                    0.10,
                    "forma parte del mismo bloque de descarte o contraste inicial"
                )

    if total_clauses > 1:
        for pat in CONTEXT_ENUM_PATTERNS:
            if re.search(pat, norm):
                return (
                    "contexto_comparativo",
                    0.18,
                    "solo enumera las opciones posibles antes de lanzar la pregunta principal"
                )

    if index < total_clauses - 1:
        for later_norm in all_clauses_norm[index + 1:]:
            starts_override = re.search(
                r"^\s*(?:pero|sin\s+embargo|no\s+obstante|en\s+cambio|mas\s+bien|sino|por\s+el\s+contrario|"
                r"por\s+lo\s+tanto|por\s+eso|asi\s+que|en\s+consecuencia|por\s+consiguiente|finalmente|al\s+final)\b",
                later_norm
            )
            later_is_negated = any(re.search(p, later_norm) for p in NEGATION_AND_EXCLUSION_PATTERNS)
            if starts_override and not later_is_negated:
                return (
                    "concesion_previa",
                    0.22,
                    "es una premisa previa que queda superada por la decision final tras el conector ('pero / por eso / finalmente')"
                )

    has_question = "?" in clause or "¿" in clause or re.search(r"\b(?:cual|como|que|donde|por\s+que)\b", norm)
    for pat in FOCAL_INTENT_PATTERNS:
        if re.search(pat, norm):
            return (
                "foco_principal",
                2.50,
                "expresa directamente el requerimiento o eleccion principal"
            )

    if has_question and total_clauses > 1:
        return (
            "foco_principal",
            2.35,
            "formula la interrogante principal de tu mensaje"
        )

    return (
        "afirmacion",
        1.0,
        "describe directamente el funcionamiento del algoritmo buscado"
    )


def generate_specific_insight(focal_text: str, full_text: str, winning_label: str) -> str:
    """
    Analiza que algoritmo, operador o escenario especifico menciono el usuario
    para redactar una explicacion viva, directa y conectada con su mensaje,
    evitando respuestas genericas o prefabricadas.
    """
    norm = normalize_text(focal_text + " " + full_text)

    if winning_label == "Heuristica":
        if re.search(r"(?:^|\s)a\*|\ba\s+estrella\b|\bf\s*\(\s*n\s*\)\s*=\s*g\s*\(\s*n\s*\)\s*\+\s*h\s*\(\s*n\s*\)", norm):
            if "gps" in norm or "mapa" in norm or "ruta" in norm or "puebla" in norm or "ciudad" in norm:
                return (
                    "En tu caso planteas un problema de navegacion y rutas con **A***: este algoritmo suma los "
                    "kilometros o costo real ya recorrido `g(n)` mas la distancia estimada en linea recta hacia el "
                    "destino `h(n)`. Asi evita explorar calles o carreteras en direccion opuesta y encuentra la ruta "
                    "optima directamente."
                )
            return (
                "Haces referencia especifica al algoritmo **A***, el cual equilibra el costo real acumulado desde "
                "el inicio `g(n)` con el costo futuro estimado `h(n)` mediante `f(n) = g(n) + h(n)`. Siempre que "
                "`h(n)` no sobreestime el costo real (heuristica admisible), A* garantiza hallar la solucion optima."
            )
        if re.search(r"\bvoraz\b|\bprimero\s+el\s+mejor\b|\bgreedy\b", norm):
            return (
                "Te refieres especificamente a la **Busqueda Voraz Primero el Mejor**, la cual se guia unicamente "
                "por `f(n) = h(n)`, eligiendo en cada paso el nodo que parece estar mas cerca de la meta. Es muy "
                "veloz, aunque a diferencia de A* puede tomar atajos aparentes que no siempre son el camino global mas corto."
            )
        if re.search(r"\bida\*|\brbfs\b|\bsma\*", norm):
            return (
                "Mencionas variantes avanzadas de busqueda informada con **memoria acotada** (`IDA*`, `RBFS` o `SMA*`), "
                "las cuales conservan el poder de guia de la funcion heuristica `h(n)` pero acotan el consumo de "
                "memoria RAM para no agotar los recursos en arboles muy profundos."
            )
        if re.search(r"\bmanhattan\b|\beuclidian[ao]\b|\bpuzzle\b|\btablero\b", norm):
            return (
                "Planteas el uso de una metrica geometrica (**distancia Manhattan o Euclidiana**) como funcion `h(n)`. "
                "Esta estimacion le da 'sentido de direccion' al agente sobre el tablero o plano, priorizando los "
                "movimientos que reducen la distancia restante hacia el estado meta."
            )
        return (
            "El nucleo de tu planteamiento reside en **guiar la exploracion con informacion del dominio** mediante "
            "una estimacion `h(n)`. En lugar de recorrer el espacio de estados a ciegas, el agente evalua que tan "
            "prometedor es cada estado para llegar a la meta en menos pasos."
        )

    if winning_label == "Ciega":
        if re.search(r"\bbfs\b|\banchura\b|\bamplitud\b|\bcola\s+fifo\b|\bfifo\b|\bnivel\s+por\s+nivel\b|\bpor\s+niveles\b", norm):
            return (
                "El metodo que describes es la **Busqueda en Anchura (BFS)**: al utilizar una estructura de **cola FIFO** "
                "(primero en entrar, primero en salir), expande todos los nodos de profundidad `d` antes de pasar al "
                "nivel `d+1`. No tiene idea de en que direccion esta la meta, pero garantiza hallar el camino con "
                "menos pasos si existe."
            )
        if re.search(r"\bdfs\b|\bprofundidad\b|\bpila\s+lifo\b|\blifo\b", norm) and not re.search(r"\blimitada\b|\biterativa\b", norm):
            return (
                "Tu planteamiento apunta a la **Busqueda en Profundidad (DFS)**: mediante una **pila LIFO** o recursion, "
                "el agente desciende por una sola rama hasta el fondo antes de retroceder (*backtracking*). Es ideal "
                "cuando el grafo es pequeno o se busca ahorrar memoria `O(bm)` sin contar con heuristicas."
            )
        if re.search(r"\biddfs\b|\bprofundizacion\s+iterativa\b|\bdls\b|\bprofundidad\s+limitada\b", norm):
            return (
                "Haces referencia a la **Profundidad Limitada (DLS) o Profundizacion Iterativa (IDDFS)**, que "
                "resuelven el riesgo de que DFS se pierda en ramas infinitas imponiendo un limite de nivel `l` que "
                "se incrementa gradualmente sin requerir informacion heuristica."
            )
        if re.search(r"\bucs\b|\bcosto\s+uniforme\b", norm):
            return (
                "Te refieres a la **Busqueda de Costo Uniforme (UCS)**, la cual expande siempre el nodo con menor "
                "costo acumulado `g(n)`. Aunque usa una cola de prioridad, sigue siendo **Busqueda Ciega** porque "
                "solo mira el costo pasado `g(n)` y no posee ninguna estimacion `h(n)` hacia la meta."
            )
        if re.search(r"\bbidireccional\b", norm):
            return (
                "Describes la **Busqueda Bidireccional**, donde dos frentes de exploracion sin heuristica avanzan "
                "simultaneamente (uno desde el inicio y otro desde la meta) hasta encontrarse a mitad de camino."
            )
        return (
            "Tu planteamiento describe un escenario donde **el agente carece de una funcion heuristica `h(n)`** que "
            "le indique que tan cerca esta del objetivo, por lo que debe inspeccionar los nodos de forma sistematica "
            "guiandose unicamente por la estructura de conexiones del grafo."
        )

    if winning_label == "Evolutiva":
        if re.search(r"\bpso\b|\benjambre\b|\baco\b|\bhormigas\b|\bferomonas\b", norm):
            return (
                "Haces referencia a metodos bioinspirados de **Inteligencia de Enjambre (`PSO` o `ACO`)**, los cuales "
                "pertenecen a la **Busqueda Evolutiva / Poblacional**: multiples agentes cooperan simultaneamente "
                "(ajustando velocidades en enjambre o depositando feromonas artificiales) para converger hacia "
                "soluciones de alta calidad sin guardar un arbol de caminos."
            )
        if re.search(r"\bcruce\b|\bcrossover\b|\bmutacion\b|\bcromosoma\b|\bseleccion\s+natural\b|\bfitness\b|\baptitud\b", norm):
            return (
                "Tu texto describe el ciclo clasico de los **Algoritmos Geneticos**: en lugar de explorar un grafo "
                "paso a paso desde un nodo inicial, se mantiene una **poblacion de individuos (cromosomas)** calificados "
                "por una funcion de aptitud (*fitness*), seleccionando a los mejores padres para cruzarlos y aplicarles "
                "**mutaciones** generacion tras generacion."
            )
        return (
            "El enfoque que solicitas trabaja con una **poblacion de soluciones en paralelo** inspirada en la "
            "evolucion biologica de Darwin. Es especialmente util cuando el espacio de busqueda es tan grande o "
            "complejo que recorrer un arbol con busqueda ciega o A* resultaria computacionalmente inviable."
        )

    return ""


def build_verdict_argument(
    user_text: str,
    winning_label: str,
    mentioned_algorithms: List[str],
    clause_breakdown: List[Dict[str, Any]],
    evidences: Dict[str, List[str]]
) -> Dict[str, Any]:
    """
    Construye un argumento conversacional, natural y especifico para lo que el
    usuario escribio, explicando por que se selecciono la etiqueta y respondiendo
    directamente a su planteamiento.
    """
    label_titles = {
        "Heuristica": "Busqueda Heuristica (Informada)",
        "Ciega": "Busqueda Ciega (No Informada)",
        "Evolutiva": "Busqueda Evolutiva (Bioinspirada)",
        "Desconocido": "Desconocido (Fuera de Dominio)"
    }

    norm_full = normalize_text(user_text)
    is_question = "?" in user_text or "¿" in user_text or bool(
        re.search(r"\b(?:cual|cuales|que\s+algoritmo|como\s+funciona|por\s+que|dime|explicame)\b", norm_full)
    )

    # Caso 1: Etiqueta Desconocido (diferenciar entre saludo/ayuda, trampa coloquial o tema ajeno)
    if winning_label == "Desconocido":
        is_greeting = bool(re.search(r"\b(?:hola|buenos\s+dias|buenas\s+tardes|buenas\s+noches|que\s+tal|como\s+estas|quien\s+eres|ayuda)\b", norm_full))
        matched_colloquial = [
            pat.replace(r"\b", "") for pat in COLLOQUIAL_TRICK_PATTERNS if re.search(pat, norm_full)
        ]

        if is_greeting and len(norm_full.split()) <= 14:
            main_reason = (
                "Se asigno la etiqueta **Desconocido** porque tu mensaje es un saludo o consulta general de "
                "conversacion y aun no describe un algoritmo de busqueda."
            )
            foundation = (
                "¡Hola! Soy el asistente clasificador entrenado con las 4 etiquetas (**Heuristica**, **Ciega**, "
                "**Evolutiva** y **Desconocido**). Puedes describirme un problema (como buscar rutas en un GPS, "
                "recorrer un arbol por niveles con BFS o evolucionar cromosomas), e incluso mencionar los 3 "
                "algoritmos en un mismo parrafo para ver como identifico tu intencion principal y argumento el veredicto."
            )
        elif matched_colloquial and len(mentioned_algorithms) > 0:
            words_str = ", ".join(f"*\"{w}\"*" for w in matched_colloquial[:3])
            main_reason = (
                f"Se selecciono la etiqueta **Desconocido** porque, aunque incluiste palabras como «a ciegas» o "
                f"«evolucion», el contexto real de tu oracion gira en torno a actividades cotidianas ({words_str}) "
                f"y no a un algoritmo computacional de Inteligencia Artificial."
            )
            foundation = (
                "El clasificador distingue entre el uso coloquial del lenguaje (como el titulo de una pelicula o "
                "una frase cotidiana) y el planteamiento tecnico de un problema de exploracion de estados."
            )
        else:
            main_reason = (
                f"Se selecciono la etiqueta **Desconocido** porque el tema que planteas (*\"{user_text[:90]}{'...' if len(user_text) > 90 else ''}\"*) "
                f"pertenece a un ambito distinto y no involucra la exploracion de grafos ni la optimizacion mediante "
                f"Busqueda Ciega, Heuristica o Evolutiva."
            )
            foundation = (
                "Cuando una consulta trata sobre otros temas generales o informaticos ajenos a los tres paradigmas "
                "entrenados, el modelo la agrupa bajo **Desconocido** para mantener la precision del clasificador."
            )

        return {
            "title": label_titles["Desconocido"],
            "main_reason": main_reason,
            "multi_mention_analysis": None,
            "clues": ["Mensaje fuera del dominio de algoritmos de busqueda"],
            "foundation": foundation,
            "full_text": f"{main_reason}\n\n{foundation}"
        }

    # Caso 2: Heuristica, Ciega o Evolutiva
    focal_evidences: List[str] = []
    for cb in clause_breakdown:
        if cb["discourse_role"] in ("foco_principal", "afirmacion"):
            for ev in cb.get("all_evidences", {}).get(winning_label, []):
                if ev not in focal_evidences:
                    focal_evidences.append(ev)

    winning_clues = focal_evidences if focal_evidences else evidences.get(winning_label, [])
    clues_str = ", ".join(winning_clues[:4]) if winning_clues else f"las caracteristicas propias de la {label_titles[winning_label]}"

    focal_clauses = [
        c["fragment"] for c in clause_breakdown
        if winning_label in c.get("mentioned_labels", [c["detected_label"]]) and c["discourse_role"] in ("foco_principal", "afirmacion")
    ]
    focal_fragment = focal_clauses[0] if focal_clauses else user_text

    # Redactar el argumento principal adaptandolo a si fue una pregunta, un contraste o un caso practico
    if is_question:
        main_reason = (
            f"La respuesta a tu pregunta corresponde a la etiqueta **{winning_label}** ({label_titles[winning_label]}). "
            f"Se selecciono este veredicto porque en la interrogante central (*\"{focal_fragment}\"*) preguntas especificamente "
            f"por **{clues_str}**."
        )
    elif len(mentioned_algorithms) >= 2:
        main_reason = (
            f"El veredicto es **{winning_label}** ({label_titles[winning_label]}) porque, al analizar tu mensaje completo, "
            f"la accion o decision que realmente deseas ejecutar se concentra en *\"{focal_fragment}\"*, donde se "
            f"especifica el uso de **{clues_str}**."
        )
    else:
        main_reason = (
            f"Se selecciono la etiqueta **{winning_label}** ({label_titles[winning_label]}) porque tu planteamiento "
            f"describe directamente el funcionamiento de **{clues_str}** dentro de *\"{focal_fragment}\"*."
        )

    # Si se mencionaron 2 o los 3 algoritmos en el mismo texto, explicar con naturalidad por que se descartaron los otros
    multi_mention_analysis = None
    if len(mentioned_algorithms) >= 2:
        discarded_algos = [a for a in mentioned_algorithms if a != winning_label]
        discarded_explanations = []
        for d_algo in discarded_algos:
            matching_clauses = [
                c for c in clause_breakdown
                if d_algo in c.get("mentioned_labels", [c["detected_label"]]) and c["discourse_role"] != "foco_principal"
            ]
            if not matching_clauses:
                matching_clauses = [
                    c for c in clause_breakdown
                    if d_algo in c.get("mentioned_labels", [c["detected_label"]])
                ]
            if matching_clauses:
                mc = matching_clauses[0]
                discarded_explanations.append(
                    f"**{d_algo}** (cuando dices *\"{mc['fragment']}\"* {mc['role_explanation']})"
                )
            else:
                discarded_explanations.append(
                    f"**{d_algo}** (mencionada solo como referencia secundaria)"
                )

        discarded_joined = "; mientras que ".join(discarded_explanations)
        if len(mentioned_algorithms) == 3:
            multi_mention_analysis = (
                f"Notaras que tu texto nombra los tres algoritmos (**Heuristica**, **Ciega** y **Evolutiva**). "
                f"Sin embargo, el modelo descarto {discarded_joined}. Por ello, el algoritmo que resuelve tu caso es **{winning_label}**."
            )
        else:
            multi_mention_analysis = (
                f"Aunque tambien nombraste a {discarded_joined}, el modelo identifico que no era el metodo que "
                f"buscabas aplicar, dandole la victoria a **{winning_label}**."
            )

    # Generar explicacion especifica conectada con el algoritmo/escenario exacto del usuario
    specific_insight = generate_specific_insight(focal_fragment, user_text, winning_label)

    parts = [main_reason]
    if multi_mention_analysis:
        parts.append(f"**Por que se descartaron las otras menciones:** {multi_mention_analysis}")
    if specific_insight:
        parts.append(f"**Aplicacion a tu planteamiento:** {specific_insight}")

    return {
        "title": label_titles[winning_label],
        "main_reason": main_reason,
        "multi_mention_analysis": multi_mention_analysis,
        "clues": winning_clues if winning_clues else [f"Planteamiento de {label_titles[winning_label]}"],
        "foundation": specific_insight,
        "full_text": "\n\n".join(parts)
    }


def classify_message(text: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    clean_text = (text or "").strip()
    effective_key = extract_mlforkids_key(api_key)

    if not clean_text:
        return {
            "label": "Desconocido",
            "source": "Modelo ML for Kids",
            "mlforkids_connected": False,
            "mentioned_algorithms": [],
            "multi_mention_detected": False,
            "all_three_mentioned": False,
            "clause_breakdown": [],
            "argument": {
                "title": "Sin texto de entrada",
                "main_reason": "Escribe una consulta o selecciona un ejemplo para analizarlo.",
                "multi_mention_analysis": None,
                "clues": [],
                "foundation": "",
                "full_text": "Por favor escribe una consulta o descripcion sobre algoritmos de busqueda para clasificarla y argumentar el veredicto."
            },
            "response": "Por favor escribe una consulta o descripcion sobre algoritmos de busqueda para clasificarla y argumentar el veredicto."
        }

    clauses = split_into_discourse_clauses(clean_text)
    all_clauses_norm = [normalize_text(c) for c in clauses]

    clause_breakdown: List[Dict[str, Any]] = []
    weighted_class_mass: Dict[str, float] = {lbl: 0.0 for lbl in LABELS}
    subordinate_classes: set = set()
    affirmative_classes: set = set()
    focal_clauses_texts: List[str] = []
    affirmative_clauses_texts: List[str] = []
    mentioned_set: set = set()
    aggregated_evidences: Dict[str, List[str]] = {lbl: [] for lbl in LABELS}

    for idx, clause_str in enumerate(clauses):
        role, role_weight, role_explanation = analyze_clause_discourse_role(
            clause_str, idx, len(clauses), all_clauses_norm
        )
        c_probs, c_evidences = LOCAL_CLASSIFIER.score_text_fragment(clause_str)
        c_mentions = [lbl for lbl in ALGORITHM_LABELS if len(c_evidences.get(lbl, [])) > 0]

        for m_lbl in c_mentions:
            mentioned_set.add(m_lbl)
            for ev in c_evidences.get(m_lbl, []):
                if ev not in aggregated_evidences[m_lbl]:
                    aggregated_evidences[m_lbl].append(ev)

        if role in ("contraste_o_negacion", "concesion_previa", "contexto_comparativo"):
            for m_lbl in c_mentions:
                subordinate_classes.add(m_lbl)
        elif role in ("foco_principal", "afirmacion"):
            for m_lbl in c_mentions:
                affirmative_classes.add(m_lbl)
            affirmative_clauses_texts.append(clause_str)
            if role == "foco_principal":
                focal_clauses_texts.append(clause_str)

        if c_mentions:
            clause_top_label = max(c_mentions, key=lambda l: c_probs[l])
        else:
            clause_top_label = max(LABELS, key=lambda l: c_probs[l])

        clause_breakdown.append({
            "fragment": clause_str,
            "detected_label": clause_top_label,
            "mentioned_labels": c_mentions,
            "discourse_role": role,
            "role_explanation": role_explanation,
            "evidences": c_evidences.get(clause_top_label, []),
            "all_evidences": c_evidences
        })

        for lbl in LABELS:
            weighted_class_mass[lbl] += c_probs[lbl] * role_weight

    mentioned_algorithms = [lbl for lbl in ALGORITHM_LABELS if lbl in mentioned_set]
    multi_mention_detected = len(mentioned_algorithms) >= 2

    if affirmative_classes and subordinate_classes:
        for sub_lbl in subordinate_classes:
            if sub_lbl not in affirmative_classes:
                weighted_class_mass[sub_lbl] *= 0.10

    total_mass = sum(weighted_class_mass.values()) or 1.0
    discourse_probs = {lbl: (weighted_class_mass[lbl] / total_mass) for lbl in LABELS}

    if mentioned_algorithms and discourse_probs["Desconocido"] < 0.65:
        algo_sum = sum(discourse_probs[l] for l in ALGORITHM_LABELS)
        if algo_sum > 0.25:
            discourse_probs["Desconocido"] *= 0.18
            norm_factor = sum(discourse_probs.values()) or 1.0
            discourse_probs = {lbl: discourse_probs[lbl] / norm_factor for lbl in LABELS}

    mlk_connected = False
    mlk_source_label = "Modelo ML for Kids Integrado (Sin cuenta)"
    final_probs = dict(discourse_probs)

    if effective_key and effective_key != "__BROWSER_LOCALSTORAGE__":
        active_texts = focal_clauses_texts if focal_clauses_texts else affirmative_clauses_texts
        query_target = " ".join(active_texts) if (multi_mention_detected and active_texts) else clean_text

        mlk_result = query_mlforkids_api(effective_key, query_target)
        if mlk_result:
            mlk_connected = True
            mlk_source_label = "Modelo ML for Kids (Nube)"
            top_pred = max(mlk_result, key=lambda x: x["confidence"])

            if top_pred["confidence"] < 45.0 and not mentioned_algorithms:
                final_probs = {"Heuristica": 0.0, "Ciega": 0.0, "Evolutiva": 0.0, "Desconocido": 1.0}
            else:
                api_probs = {lbl: 0.01 for lbl in LABELS}
                for item in mlk_result:
                    lbl = item["class_name"]
                    if lbl in api_probs:
                        api_probs[lbl] = max(api_probs[lbl], item["confidence"] / 100.0)

                if affirmative_classes and subordinate_classes:
                    for sub_lbl in subordinate_classes:
                        if sub_lbl not in affirmative_classes:
                            api_probs[sub_lbl] *= 0.08

                api_sum = sum(api_probs.values()) or 1.0
                api_probs = {lbl: api_probs[lbl] / api_sum for lbl in LABELS}

                alpha = 0.80
                for lbl in LABELS:
                    final_probs[lbl] = (alpha * api_probs[lbl]) + ((1.0 - alpha) * discourse_probs[lbl])
                f_sum = sum(final_probs.values()) or 1.0
                final_probs = {lbl: final_probs[lbl] / f_sum for lbl in LABELS}

    winning_label = max(LABELS, key=lambda l: final_probs[l])

    argument_obj = build_verdict_argument(
        user_text=clean_text,
        winning_label=winning_label,
        mentioned_algorithms=mentioned_algorithms,
        clause_breakdown=clause_breakdown,
        evidences=aggregated_evidences
    )

    return {
        "label": winning_label,
        "source": mlk_source_label,
        "mlforkids_connected": mlk_connected,
        "mentioned_algorithms": mentioned_algorithms,
        "multi_mention_detected": multi_mention_detected,
        "all_three_mentioned": len(mentioned_algorithms) == 3,
        "clause_breakdown": clause_breakdown,
        "evidences": aggregated_evidences,
        "argument": argument_obj,
        "response": argument_obj["full_text"]
    }
