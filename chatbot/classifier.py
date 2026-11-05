"""
chatbot/classifier.py
Motor clasificador de texto probabilistico (Naive Bayes multinomial con N-gramas
y matching de patrones de dominio) compatible con Machine Learning for Kids (ML for Kids).
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

from chatbot.corpus import LABELS, ALGORITHM_LABELS, TRAINING_CORPUS

DEFAULT_MLFORKIDS_API_KEY = os.environ.get("MLFORKIDS_API_KEY", "").strip()


def normalize_text(text: str) -> str:
    """Normaliza texto a minusculas eliminando diacriticos y signos repetidos."""
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
    (#!/mlproject/localstorage/...), devuelve __BROWSER_LOCALSTORAGE__.
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
    """Normaliza variantes textuales a una de las 4 etiquetas oficiales."""
    norm = normalize_text(raw_label).replace("_", " ").replace("-", " ")
    if "heurist" in norm or ("informad" in norm and "no informad" not in norm):
        return "Heuristica"
    if "cieg" in norm or "no informad" in norm:
        return "Ciega"
    if "evolut" in norm or "genet" in norm or "bioinspir" in norm:
        return "Evolutiva"
    return "Desconocido"


BLIND_ABSENCE_OF_HEURISTIC_REGEX = re.compile(
    r"\b(?:sin\s+(?:ningun\s+|ninguna\s+|usar\s+|emplear\s+|utilizar\s+|tener\s+|contar\s+con\s+)?|"
    r"no\s+(?:usa|usan|utiliza|utilizan|emplea|emplean|tiene|tienen|cuenta\s+con|requiere|dispone\s+de)\s+(?:ningun\s+|ninguna\s+)?|"
    r"(?:carece|ausencia|falta)\s+de\s+)"
    r"(?:conocimiento|informacion|funcion\s+heuristica|formula\s+heuristica|heuristica|heuristicas|estimacion|guia)"
    r"(?:\s+heuristic[ao]s?|\s+adicional(?:es)?|\s+del\s+problema|\s+del\s+dominio|\s+h\s*\(\s*n\s*\)|\s+h\s+de\s+n)?\b"
)


DOMAIN_PATTERNS: Dict[str, List[Tuple[str, float, str]]] = {
    "Heuristica": [
        (r"\bbusqueda\s+heuristic[ao]s?\b", 4.6, "Busqueda Heuristica"),
        (r"\bbusqueda\s+informad[ao]s?\b|\balgoritmos?\s+de\s+busqueda\s+informad[ao]\b|\bestrategia\s+informada\b", 4.6, "Busqueda Informada"),
        (r"\bfuncion\s+heuristic[ao]\b|\bfunciones\s+heuristicas\b", 4.5, "funcion heuristica"),
        (r"\bheuristic[ao]s?\s+admisibles?\b|\bcondicion\s+de\s+admisibilidad\b|\badmisibilidad\b", 4.5, "heuristica admisible"),
        (r"\bheuristic[ao]s?\s+consistentes?\b|\bconsistencia\s+heuristica\b|\bdesigualdad\s+triangular\b", 4.5, "heuristica consistente / desigualdad triangular"),
        (r"\bheuristic[ao]\s+dominante\b|\bdomina\s+a\s+otra\s+heuristica\b", 4.5, "heuristica dominante"),
        (r"\bfactor\s+de\s+ramificacion\s+efectivo\b|\bb\s+estrella\b", 4.4, "factor de ramificacion efectivo (b*)"),
        (r"\bproblema\s+relajado\b|\brelajacion\s+de\s+restricciones\b|\bsubproblemas\s+relajados\b", 4.3, "heuristica por problema relajado"),
        (r"\bbases?\s+de\s+datos\s+de\s+patrones\b", 4.5, "bases de datos de patrones"),
        (r"\bpathmax\b", 4.5, "correccion Pathmax"),
        (r"\bheuristicas?\s+alt\b|\bpuntos\s+de\s+referencia\b", 4.4, "heuristicas ALT / puntos de referencia"),
        (r"\bheuristic[ao]s?\b", 3.0, "estimacion heuristica"),
        (r"(?:^|\s|['\"(\[])a\*(?=$|\s|[.,;:?!)'\"\]])", 4.7, "algoritmo A*"),
        (r"\balgoritmo\s+a\s+estrella\b|\ba\s+estrella\b|\ba\s+asterisco\b", 4.7, "algoritmo A estrella (A*)"),
        (r"\bida\*|\bida\s+estrella\b", 4.7, "algoritmo IDA*"),
        (r"\bsma\*|\bsma\s+estrella\b", 4.7, "algoritmo SMA*"),
        (r"\blpa\s+estrella\b|\blpa\*", 4.7, "algoritmo LPA*"),
        (r"\bd\s+estrella\s+lite\b|\bd\*\s*lite\b", 4.7, "algoritmo D* Lite"),
        (r"\blrta\s+estrella\b|\blrta\*", 4.7, "algoritmo LRTA*"),
        (r"\brbfs\b|\bbusqueda\s+primero\s+el\s+mejor\s+recursiva\b", 4.6, "algoritmo RBFS"),
        (r"\bbusqueda\s+voraz\b|\balgoritmo\s+voraz\b|\balgoritmos\s+voraces\b", 4.4, "Busqueda Voraz"),
        (r"\bprimero\s+el\s+mejor\b|\bgreedy\s+best[\s-]first\b", 4.4, "estrategia Primero el Mejor"),
        (r"\bf\s*\(\s*n\s*\)\s*=\s*g\s*\(\s*n\s*\)\s*\+\s*h\s*\(\s*n\s*\)", 5.0, "formula f(n) = g(n) + h(n)"),
        (r"\bh\s*\(\s*n\s*\)|\bh\s+de\s+n\b|\bh\s+estrella\b", 4.0, "funcion heuristica h(n)"),
        (r"\bf\s*\(\s*n\s*\)|\bf\s+de\s+n\b|\bvalor\s+f\b|\bvalores\s+f\b|\blimite\s+f\b|\bumbral\s+f\b", 3.6, "evaluacion f(n)"),
        (r"\bdistancia\s+manhattan\b", 4.4, "distancia Manhattan"),
        (r"\bdistancia\s+euclidian[ao]\b|\blinea\s+recta\b", 4.0, "distancia en linea recta (Euclidiana)"),
        (r"\bfichas\s+fuera\s+de\s+lugar\b|\bfichas\s+descolocadas\b|\bdistancia\s+de\s+hamming\b", 4.4, "heuristica de fichas fuera de lugar (Hamming)"),
        (r"\bdistancia\s+de\s+chebyshev\b|\bdistancia\s+octil\b|\bu\s+octil\b", 4.4, "distancia de Chebyshev / octil"),
        (r"\bconflicto\s+lineal\b", 4.4, "heuristica de conflicto lineal"),
        (r"\bbusqueda\s+en\s+haz\b|\bbeam\s+search\b|\bbusqueda\s+local\s+en\s+haz\b|\bancho\s+del\s+haz\b", 4.5, "Busqueda en Haz (Beam Search)"),
        (r"\bascenso\s+de\s+colinas\b|\bhill\s+climbing\b", 4.6, "Ascenso de Colinas (Hill Climbing)"),
        (r"\bmaximos?\s+locales?\b|\boptimos?\s+locales?\b|\bmesetas?\s+planas?\b|\bcrestas?\b|\bmovimientos?\s+laterales?\b", 3.8, "paisaje de busqueda local (optimos locales / mesetas)"),
        (r"\brecocido\s+simulado\b|\bsimulated\s+annealing\b|\bplan\s+de\s+enfriamiento\b|\bcriterio\s+de\s+metropolis\b", 4.6, "Recocido Simulado (Simulated Annealing)"),
        (r"\bbusqueda\s+tabu\b|\blista\s+tabu\b|\btenencia\s+tabu\b|\bcriterio\s+de\s+aspiracion\b", 4.6, "Busqueda Tabu"),
        (r"\bbusqueda\s+de\s+vecindario\s+variable\b|\bvns\b", 4.6, "Busqueda de Vecindario Variable (VNS)"),
        (r"\bmin\s+conflicts\b|\bminimos\s+conflictos\b", 4.5, "heuristica Min-Conflicts"),
        (r"\bestima(?:r|cion|ndo|ciones)?\s+(?:la\s+|el\s+|que\s+tan\s+)?(?:distancia|costo|cercania|cerca)\b", 3.5, "estimacion de costo/distancia hacia la meta"),
        (r"\bpathfinding\b|\bmallas\s+de\s+navegacion\b|\bmapa\s+gps\b|\bcoordenadas\s+gps\b", 3.6, "calculo de rutas con guia heuristica"),
    ],
    "Ciega": [
        (r"\bbusqueda\s+cieg[ao]s?\b|\balgoritmos?\s+ciegos?\b|\barbol\s+ciego\b|\bagente\s+ciego\b|\borden\s+ciego\b|\bmetodo\s+ciego\b", 4.6, "Busqueda Ciega"),
        (r"\bbusqueda\s+no\s+informad[ao]s?\b|\balgoritmos?\s+no\s+informados?\b|\bbusqueda\s+en\s+arbol\s+no\s+informada\b", 4.6, "Busqueda No Informada"),
        (r"\bbusqueda\s+a\s+ciegas\b|\ba\s+ciegas\b", 3.8, "exploracion a ciegas"),
        (r"\bbusqueda\s+por\s+fuerza\s+bruta\b|\bgeneracion\s+y\s+prueba\b|\bbusqueda\s+exhaustiva\s+sin\s+guia\b", 4.5, "Busqueda por Fuerza Bruta / Exhaustiva"),
        (r"\bbusqueda\s+en\s+anchura\b|\bbusqueda\s+en\s+amplitud\b|\bbusqueda\s+no\s+informada\s+en\s+anchura\b", 4.6, "Busqueda en Anchura (BFS)"),
        (r"\bbusqueda\s+primero\s+en\s+profundidad\b|\bbusqueda\s+en\s+profundidad\b", 4.6, "Busqueda en Profundidad (DFS)"),
        (r"\bbusqueda\s+de\s+costo\s+uniforme\b|\bcosto\s+uniforme\b|\biducs\b", 4.6, "Busqueda de Costo Uniforme (UCS)"),
        (r"\bprofundidad\s+limitada\b", 4.5, "Busqueda en Profundidad Limitada (DLS)"),
        (r"\bprofundizacion\s+iterativa\b", 4.6, "Busqueda en Profundizacion Iterativa (IDDFS)"),
        (r"\bbusqueda\s+bidireccional\b", 4.5, "Busqueda Bidireccional"),
        (r"\bbfs\b", 4.5, "algoritmo BFS"),
        (r"\bdfs\b", 4.5, "algoritmo DFS"),
        (r"\bucs\b", 4.4, "algoritmo UCS"),
        (r"\bdls\b", 4.3, "algoritmo DLS"),
        (r"\biddfs\b|\bids\b", 4.5, "algoritmo IDDFS"),
        (r"\bcola\s+fifo\b", 4.2, "cola FIFO"),
        (r"\bpila\s+lifo\b|\bestructura\s+lifo\b", 4.2, "pila LIFO"),
        (r"\bbacktracking\b|\bretroceso\s+cronologico\b", 4.0, "retroceso cronologico (backtracking en DFS)"),
        (r"\bnivel\s+por\s+nivel\b|\bpor\s+niveles\b|\bcapas\s+concentricas\b", 3.6, "exploracion nivel por nivel"),
        (r"\bmisioneros\s+y\s+los\s+canibales\b|\bjarras\s+de\s+agua\b|\bregla\s+de\s+la\s+mano\s+derecha\b", 4.2, "problema clasico de busqueda ciega"),
        (r"\binterseccion\s+de\s+fronteras\b|\bchoque\s+de\s+fronteras\b", 4.2, "interseccion de fronteras en busqueda bidireccional"),
        (r"\bcaja\s+negra\s+donde\s+solo\s+se\s+puede\s+avanzar\s+paso\s+a\s+paso\b", 4.2, "exploracion de espacio como caja negra"),
    ],
    "Evolutiva": [
        (r"\bbusqueda\s+evolutiv[ao]s?\b|\balgoritmos?\s+evolutiv[ao]s?\b|\bciclo\s+evolutivo\b|\bmod[e]?lo\s+evolutivo\b|\bisla\s+evolutiva\b", 4.6, "Busqueda Evolutiva"),
        (r"\balgoritmos?\s+genetic[ao]s?\b", 4.7, "Algoritmos Geneticos"),
        (r"\bcomputacion\s+evolutiva\b", 4.6, "Computacion Evolutiva"),
        (r"\bestrategias?\s+evolutiv[ao]s?\b|\bmu\s+coma\s+lambda\b|\bmu\s+mas\s+lambda\b|\brechenberg\b|\bcma\s+es\b", 4.6, "Estrategias Evolutivas"),
        (r"\bprogramacion\s+genetica\b|\bjohn\s+koza\b|\barboles\s+sintacticos\b|\bbloat\b|\bpresion\s+de\s+parsimonia\b", 4.6, "Programacion Genetica"),
        (r"\bprogramacion\s+evolutiva\b|\blawrence\s+fogel\b", 4.6, "Programacion Evolutiva"),
        (r"\bevolucion\s+diferencial\b", 4.6, "Evolucion Diferencial"),
        (r"\balgoritmos?\s+memetic[ao]s?\b|\befecto\s+baldwin\b|\bevolucion\s+lamarckiana\b", 4.6, "Algoritmos Memeticos"),
        (r"\bnsga\s+dos\b|\bdominancia\s+de\s+pareto\b|\bsentido\s+de\s+pareto\b|\bdistancia\s+de\s+hacinamiento\b", 4.5, "Optimizacion Evolutiva Multiobjetivo (NSGA-II / Pareto)"),
        (r"\bteorema\s+de\s+los\s+esquemas\b|\bjohn\s+holland\b|\bbloques\s+constructivos\b|\bplantilla\s+cromosomica\b", 4.6, "Teorema de los Esquemas y Bloques Constructivos"),
        (r"\binteligencia\s+de\s+enjambre\b|\benjambre\s+de\s+particulas\b|\bpso\b|\bcolonia\s+de\s+hormigas\b|\baco\b", 4.5, "Inteligencia de Enjambre / Bioinspirada"),
        (r"\bseleccion\s+natural\b|\bsupervivencia\s+del\s+mas\s+apto\b|\bevolucion\s+biologica\s+darwiniana\b", 4.3, "seleccion natural darwiniana"),
        (r"\bseleccion\s+por\s+(?:ruleta|torneo|rangos|truncamiento)\b|\bseleccion\s+de\s+boltzmann\b|\bmuestreo\s+estocastico\s+universal\b|\bescalamiento\s+sigma\b", 4.5, "operador de seleccion evolutiva"),
        (r"\bpresion\s+selectiva\b|\bdiversidad\s+genetica\b|\bderiva\s+genetica\b|\bepistasis\b|\bconvergencia\s+genotipica\b|\belitismo\b|\bniching\b|\bcrowding\s+determinista\b", 4.4, "dinamica poblacional y genetica"),
        (r"\bfuncion\s+de\s+aptitud\b|\bfitness\b", 4.4, "funcion de aptitud (fitness)"),
        (r"\bcruce\b|\bcrossover\b|\brecombinacion\b|\bpmx\b|\bblx\s+alfa\b|\bsbx\b|\bcycle\s+crossover\b", 4.2, "operador de cruce / crossover"),
        (r"\bmutacion(?:es)?\b|\bbit\s+flip\b|\bmutacion\s+gaussiana\b|\bmutacion\s+de\s+subarbol\b|\bdesorden\s+o\s+scramble\b", 4.2, "operador de mutacion"),
        (r"\bcromosomas?\b|\bcadena\s+cromosomica\b|\bgenes\b|\balelos?\b|\blocus\b|\bgenotipo\b|\bfenotipo\b|\bcodigo\s+gray\b", 4.5, "codificacion genetica (cromosoma / gen / alelo / genotipo / fenotipo)"),
        (r"\bpoblacion\s+de\s+(?:soluciones|individuos|padres|candidatos)\b|\bsubpoblaciones\b|\bcoevolucion\b|\bmod[e]?lo\s+isla\b|\btasa\s+de\s+migracion\b", 4.4, "evolucion de poblaciones"),
        (r"\bgeneraciones\s+sucesivas\b|\breemplazo\s+generacional\b|\bciclo\s+generacional\b", 4.0, "evolucion a traves de generaciones"),
    ],
    "Desconocido": [
        (r"\bordenamiento\s+(?:burbuja|rapido|por\s+insercion|por\s+seleccion|por\s+residuos|por\s+cubetas|topologico)\b|\balgoritmo\s+de\s+ordenamiento\b", 5.2, "algoritmo de ordenamiento clasico"),
        (r"\bquicksort\b|\bmergesort\b|\bheapsort\b|\bradix\s+sort\b|\bcounting\s+sort\b|\bshellsort\b|\bbucket\s+sort\b|\btimsort\b", 5.4, "algoritmo de ordenamiento de arreglos"),
        (r"\bbusqueda\s+(?:secuencial|lineal|binaria|dicotomica|por\s+interpolacion|exponencial|por\s+saltos|vectorial)\b|\bgalloping\s+search\b|\bjump\s+search\b|\bskip\s+list\b", 5.4, "busqueda clasica en arreglos o estructuras de datos"),
        (r"\btablas?\s+hash\b|\brehashing\b|\bsondeo\s+cuadratico\b|\bdoble\s+hashing\b|\bfiltro\s+de\s+bloom\b", 5.2, "estructuras de dispersion (tablas hash / filtro de Bloom)"),
        (r"\barbol\s+binario\s+de\s+busqueda\b|\babb\b|\barboles\s+avl\b|\brojo\s+negro\b|\barbol\s+b\b|\barbol\s+trie\b|\barbol\s+fenwick\b|\barbol\s+de\s+segmentos\b|\bsegment\s+tree\b|\brecorrido\s+(?:inorden|preorden|postorden)\b", 5.4, "estructuras de datos arboreas (ABB / AVL / Trie / B-Tree)"),
        (r"\blista\s+(?:simplemente|doblemente)\s+enlazada\b|\bunion\s+find\b|\bconjuntos\s+disjuntos\b", 5.2, "estructuras de datos lineales y conjuntos disjuntos"),
        (r"\bboyer\s+moore\b|\bknuth\s+morris\s+pratt\b|\bkmp\b|\brabin\s+karp\b|\baho\s+corasick\b|\blevenshtein\b", 5.4, "algoritmos de busqueda de cadenas y procesamiento de texto"),
        (r"\bkruskal\b|\balgoritmo\s+de\s+prim\b|\bbellman\s+ford\b|\bfloyd\s+warshall\b|\balgoritmo\s+de\s+tarjan\b|\bford\s+fulkerson\b|\bedmonds\s+karp\b", 5.4, "algoritmos clasicos de teoria de grafos y flujo en redes"),
        (r"\bbanquero\s+de\s+dijkstra\b|\binterbloqueos?\b|\bdeadlock\b|\bsemaforo\b|\bmutex\b|\bpaginacion\s+de\s+memoria\b|\bround\s+robin\b|\bcontext\s+switch\b|\bcambio\s+de\s+contexto\b|\bpipelining\b|\binterrupcion\s+de\s+hardware\b|\bmemoria\s+cache\b", 5.4, "sistemas operativos y arquitectura de computadoras"),
        (r"\bbase\s+de\s+datos\s+relacional\b|\bsql\b|\bprimary\s+key\b|\bforeign\s+key\b|\bnormalizacion\s+de\s+bases\b|\bpropiedades\s+acid\b|\bnosql\b|\bmongodb\b|\bteorema\s+cap\b|\binner\s+join\b", 5.4, "sistemas de bases de datos (SQL / NoSQL)"),
        (r"\bmod[e]?lo\s+osi\b|\bprotocolo\s+(?:tcp|udp|http|https|arp|dhcp|oauth)\b|\bdireccion(?:es)?\s+ip\b|\bdns\b|\bmascara\s+de\s+subred\b|\btraduccion\s+de\s+direcciones\s+de\s+red\s+nat\b|\bcortafuegos\b|\bfirewall\b", 5.4, "redes de computadoras y protocolos de comunicacion"),
        (r"\bdocker\b|\bcontrol\s+de\s+versiones\s+git\b|\borientada\s+a\s+objetos\b|\bgarbage\s+collector\b|\bcompilador\b|\brecursividad\b|\bprogramacion\s+dinamica\b|\bdivide\s+y\s+venceras\b|\bexpresion\s+regular\b|\bformato\s+json\b|\brestful\b|\bpruebas\s+unitarias\b|\bintegracion\s+continua\b|\bsingleton\b|\bresponsabilidad\s+unica\b|\bbig\s+o\b|\bmochila\s+fraccionaria\b|\bcodificacion\s+de\s+huffman\b|\bsimilitud\s+de\s+coseno\b", 5.4, "ingenieria de software, estructuras y algoritmia general"),
        (r"\bcifrado\s+(?:simetrico|asimetrico)\b|\baes\b|\brsa\b|\bsha\s+256\b|\binyeccion\s+sql\b|\bcross\s+site\s+scripting\b|\bxss\b|\bjson\s+web\s+token\b|\bjwt\b", 5.4, "seguridad informatica y criptografia"),
    ]
}

COLLOQUIAL_TRICK_PATTERNS = [
    r"\bpelicula\b", r"\bcine\b", r"\breceta\b", r"\bpizza\b", r"\bcocina\b",
    r"\bfutbol\b", r"\bpartido\b", r"\bclima\b", r"\bimpuestos\b", r"\bvacaciones\b"
]


class LocalMLForKidsClassifier:
    """
    Clasificador local entrenado con los 420 ejemplos oficiales de las 4 cubetas
    (Heuristica, Ciega, Evolutiva, Desconocido) y reentrenable en vivo.
    """

    def __init__(self, corpus: Dict[str, List[str]]) -> None:
        self.corpus = corpus
        self.class_doc_counts: Dict[str, int] = {}
        self.class_token_counts: Dict[str, Counter] = {}
        self.class_total_tokens: Dict[str, int] = {}
        self.exact_lookup: Dict[str, str] = {}
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
        tokens = [
            t for t in raw_tokens
            if (t not in stopwords and len(t) > 1) or t in {"a*", "h(n)", "g(n)", "f(n)", "b", "d", "m", "l", "h", "g", "f"}
        ]
        bigrams = [f"{tokens[i]}_{tokens[i + 1]}" for i in range(len(tokens) - 1)]
        trigrams = [f"{tokens[i]}_{tokens[i + 1]}_{tokens[i + 2]}" for i in range(len(tokens) - 2)]
        return tokens + bigrams + trigrams

    def retrain(self) -> None:
        self.class_doc_counts.clear()
        self.class_token_counts.clear()
        self.class_total_tokens.clear()
        self.exact_lookup.clear()
        self.vocab.clear()
        self.total_docs = 0

        for label, texts in self.corpus.items():
            self.class_doc_counts[label] = len(texts)
            self.total_docs += len(texts)
            token_counter: Counter = Counter()
            for doc in texts:
                norm_doc = normalize_text(doc).strip(" .,;:?!")
                if norm_doc:
                    self.exact_lookup[norm_doc] = label
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
        norm_clean = norm.strip(" .,;:?!")
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
                ll += math.log((count + 0.35) / (total_cls_tokens + 0.35 * vocab_size))
            log_scores[label] = ll

        max_nb = max(log_scores.values())
        nb_scaled = {lbl: (log_scores[lbl] - max_nb) * 0.55 for lbl in LABELS}

        domain_scores: Dict[str, float] = {lbl: 0.0 for lbl in LABELS}
        evidences: Dict[str, List[str]] = {lbl: [] for lbl in LABELS}

        if norm_clean in self.exact_lookup:
            exact_lbl = self.exact_lookup[norm_clean]
            domain_scores[exact_lbl] += 6.0

        first_person_reject = re.search(r"\bno\s+(?:quiero|queremos|prefiero|necesito|usaremos)\b", norm)
        norm_for_heuristica = norm
        if BLIND_ABSENCE_OF_HEURISTIC_REGEX.search(norm) and not first_person_reject:
            domain_scores["Ciega"] += 4.8
            evidences["Ciega"].append("exploracion sin informacion heuristica ni conocimiento adicional del dominio")
            norm_for_heuristica = BLIND_ABSENCE_OF_HEURISTIC_REGEX.sub(" ", norm)

        for lbl_key, pattern_list in DOMAIN_PATTERNS.items():
            target_norm = norm_for_heuristica if lbl_key == "Heuristica" else norm
            for regex_pat, weight, description in pattern_list:
                if re.search(regex_pat, target_norm):
                    domain_scores[lbl_key] += weight
                    if description not in evidences[lbl_key]:
                        evidences[lbl_key].append(description)

        colloquial_hits = sum(1 for pat in COLLOQUIAL_TRICK_PATTERNS if re.search(pat, norm))
        total_algo_score = sum(domain_scores[lbl] for lbl in ALGORITHM_LABELS)
        nb_top_label = max(LABELS, key=lambda l: log_scores[l])
        sorted_nb = sorted(log_scores.values(), reverse=True)
        nb_margin = sorted_nb[0] - sorted_nb[1] if len(sorted_nb) > 1 else 0.0

        if colloquial_hits >= 2 and total_algo_score < 4.5:
            domain_scores["Desconocido"] += 6.5
        elif total_algo_score == 0.0 and domain_scores["Desconocido"] == 0.0:
            if nb_top_label == "Desconocido" or nb_margin < 2.2 or len(ngrams) <= 3:
                domain_scores["Desconocido"] += 4.5
            else:
                domain_scores[nb_top_label] += 2.5

        combined_logits: Dict[str, float] = {}
        for lbl in LABELS:
            combined_logits[lbl] = nb_scaled[lbl] + domain_scores[lbl]

        max_logit = max(combined_logits.values())
        exp_scores = {lbl: math.exp(max(-40.0, combined_logits[lbl] - max_logit)) for lbl in LABELS}
        sum_exp = sum(exp_scores.values())
        probs = {lbl: (exp_scores[lbl] / sum_exp) for lbl in LABELS}

        return probs, evidences


LOCAL_CLASSIFIER = LocalMLForKidsClassifier(TRAINING_CORPUS)


def check_mlforkids_status(raw_key: str, timeout: float = 4.5) -> Dict[str, Any]:
    """Verifica conexion con el servicio de ML for Kids o reporta modo local."""
    clean_key = extract_mlforkids_key(raw_key)
    if clean_key == "__BROWSER_LOCALSTORAGE__":
        return {
            "connected": False,
            "key": "",
            "message": (
                "Pegaste la URL del navegador de un proyecto 'Sin cuenta' (localstorage). "
                "En ML for Kids sin cuenta, el modelo vive solo dentro de la pestaña de ese sitio y no genera API externa. "
                "Por ello, tienes activo aqui mismo el Modelo ML for Kids Integrado con los 420 ejemplos de tus 4 etiquetas."
            )
        }

    if not clean_key:
        return {
            "connected": False,
            "key": "",
            "message": "Modo sin cuenta activo: el chatbot opera con el modelo entrenado con tus 420 ejemplos de las 4 etiquetas."
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
            "Se mantiene activo el Modelo ML for Kids Integrado con tus 420 ejemplos de entrenamiento."
        )
    }


def query_mlforkids_api(raw_key: str, text: str, timeout: float = 4.5) -> Optional[List[Dict[str, Any]]]:
    """Consulta el endpoint scratch de clasificacion de ML for Kids."""
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
