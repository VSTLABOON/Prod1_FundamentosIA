"""
chatbot/argumentation.py
Generador de argumentos conversacionales y justificaciones pedagogicas.
Elabora un razonamiento detallado, amigable y riguroso que explica por que el modelo
asigno determinada etiqueta (Heuristica, Ciega, Evolutiva o Desconocido), destacando
las pistas tecnicas encontradas y explicando el motivo del descarte en caso de multi-mencion.
"""

import re
from typing import List, Dict, Any

from chatbot.classifier import normalize_text, COLLOQUIAL_TRICK_PATTERNS
from chatbot.corpus import LABELS


def generate_specific_insight(focal_text: str, full_text: str, winning_label: str) -> str:
    """
    Analiza que algoritmo, operador o escenario especifico menciono el usuario
    para redactar una explicacion viva, directa y conectada con su mensaje.
    """
    norm = normalize_text(focal_text + " " + full_text)

    if winning_label == "Heuristica":
        if re.search(r"\bascenso\s+de\s+colinas\b|\bhill\s+climbing\b|\bmovimiento\s+lateral\b|\bcresta\b|\bmeseta\b|\bmin\s+conflicts\b|\bminimos\s+conflictos\b", norm):
            return (
                "Tu enunciado aborda la **Busqueda Local Heuristica** (**Hill Climbing / Ascenso de Colinas** o **Min-Conflicts**): "
                "el agente evalua la calidad heuristica de los estados vecinos inmediatos y avanza en direccion de la mejora "
                "sin almacenar el arbol de rutas en memoria, enfrentando retos como maximos locales, mesetas y crestas."
            )
        if re.search(r"\brecocido\s+simulado\b|\bsimulated\s+annealing\b|\bmetropolis\b|\benfriamiento\b", norm):
            return (
                "Te refieres al **Recocido Simulado (Simulated Annealing)** dentro de la busqueda heuristica local: "
                "inspirado en la metalurgia, acepta movimientos hacia estados peores con una probabilidad de Boltzmann "
                "controlada por la temperatura `T` para escapar de optimos locales antes de enfriarse."
            )
        if re.search(r"\bbusqueda\s+tabu\b|\blista\s+tabu\b|\btenencia\s+tabu\b|\baspiracion\b|\bvecindario\s+variable\b|\bvns\b", norm):
            return (
                "Haces referencia a metaheuristicas de trayectoria como la **Busqueda Tabu** o **Vecindario Variable (VNS)**: "
                "guian la busqueda con una funcion de evaluacion heuristica y emplean estructuras de memoria (lista tabu, "
                "criterio de aspiracion o cambio de vecindario) para no ciclarse en optimos locales."
            )
        if re.search(r"\bbusqueda\s+en\s+haz\b|\bbeam\s+search\b|\bancho\s+del\s+haz\b", norm):
            return (
                "Describes la **Busqueda en Haz (Beam Search)**, un metodo heuristico de memoria acotada que conserva "
                "unicamente los `beta` nodos mejor evaluados por `h(n)` en cada nivel, podando el resto de la frontera."
            )
        if re.search(r"\bida\*|\bida\s+estrella\b|\brbfs\b|\bsma\*|\bsma\s+estrella\b", norm):
            return (
                "Mencionas algoritmos de **busqueda heuristica con memoria acotada** (`IDA*`, `RBFS` o `SMA*`), "
                "los cuales aprovechan la funcion de evaluacion `f(n) = g(n) + h(n)` respaldando valores `f` en los "
                "nodos padres o cortando por umbrales para no agotar la memoria RAM."
            )
        if re.search(r"\blpa\s+estrella\b|\blpa\*|\bd\s+estrella\s+lite\b|\bd\*\s*lite\b|\blrta\s+estrella\b|\blrta\*", norm):
            return (
                "Haces referencia a algoritmos de **busqueda heuristica incremental o en tiempo real** (`LPA*`, `D* Lite` o `LRTA*`), "
                "disenados para actualizar los valores heuristicos y replanificar rutas dinamicamente cuando el agente descubre obstaculos."
            )
        if re.search(r"(?:^|\s)a\*|\ba\s+estrella\b|\ba\s+asterisco\b|\bf\s*\(\s*n\s*\)\s*=\s*g\s*\(\s*n\s*\)\s*\+\s*h\s*\(\s*n\s*\)", norm):
            if "gps" in norm or "mapa" in norm or "ruta" in norm or "puebla" in norm or "carretera" in norm:
                return (
                    "En tu caso planteas un problema de navegacion y rutas con **A***: este algoritmo suma los "
                    "kilometros o costo real ya recorrido `g(n)` mas la distancia estimada en linea recta hacia el "
                    "destino `h(n)`. Asi evita explorar calles o carreteras en direccion opuesta y encuentra la ruta optima."
                )
            return (
                "Haces referencia especifica al algoritmo **A*** (`A estrella`), el cual combina el costo exacto acumulado "
                "`g(n)` con el costo heuristico estimado `h(n)` mediante `f(n) = g(n) + h(n)`. Con una heuristica "
                "admisible y consistente, A* es completo, optimo y optimamente eficiente."
            )
        if re.search(r"\bvoraz\b|\bprimero\s+el\s+mejor\b|\bgreedy\b", norm):
            return (
                "Te refieres a la **Busqueda Voraz Primero el Mejor**, la cual ordena la cola de prioridad usando "
                "unicamente la estimacion heuristica `h(n)` sin considerar el costo ya recorrido `g(n)`, buscando "
                "avanzar rapido hacia la meta aunque no garantice optimalidad."
            )
        if re.search(r"\bmanhattan\b|\beuclidian[ao]\b|\bhamming\b|\bfichas\s+fuera\b|\bchebyshev\b|\boctil\b|\bconflicto\s+lineal\b|\bpatrones\b|\bproblema\s+relajado\b", norm):
            return (
                "Tu enunciado se centra en el **diseno y propiedades de funciones heuristicas `h(n)`** (como distancia "
                "Manhattan, Euclidiana, Hamming, Chebyshev/octil, conflicto lineal o bases de datos de patrones obtenidas "
                "de problemas relajados) para guiar la exploracion informada con alta precision."
            )
        return (
            "El nucleo de tu planteamiento reside en **guiar la exploracion con conocimiento especifico del dominio** "
            "mediante una funcion heuristica `h(n)`, cumpliendo propiedades como admisibilidad y consistencia para "
            "reducir drasticamente el numero de nodos expandidos."
        )

    if winning_label == "Ciega":
        if re.search(r"\bbfs\b|\banchura\b|\bamplitud\b|\bcola\s+fifo\b|\bcapas\s+concentricas\b", norm):
            return (
                "El metodo que describes es la **Busqueda en Anchura (BFS)**: al utilizar una estructura de **cola FIFO** "
                "(primero en entrar, primero en salir), expande el arbol por capas concentricas nivel por nivel. "
                "Es completa y optima cuando todos los costos de paso son iguales, pero su memoria crece de forma exponencial `O(b^d)`."
            )
        if re.search(r"\bdfs\b|\bprimero\s+en\s+profundidad\b|\bpila\s+lifo\b|\bbacktracking\b|\bretroceso\s+cronologico\b", norm) and not re.search(r"\blimitada\b|\biterativa\b", norm):
            return (
                "Tu planteamiento apunta a la **Busqueda en Profundidad (DFS)**: mediante una **pila LIFO** o recursion, "
                "desciende hasta el nodo hoja mas profundo y aplica retroceso (*backtracking*) al topar con un callejon "
                "sin salida, destacando por su bajo consumo de memoria lineal `O(bm)`."
            )
        if re.search(r"\biddfs\b|\bids\b|\bprofundizacion\s+iterativa\b|\bdls\b|\bprofundidad\s+limitada\b|\bcutoff\b", norm):
            return (
                "Haces referencia a la **Profundidad Limitada (DLS) o Profundizacion Iterativa (IDDFS / IDS)**: "
                "imponen un limite de nivel `L` (incrementandolo de uno en uno en IDDFS) para combinar la completitud "
                "y optimalidad de BFS con la memoria lineal `O(bd)` de DFS sin usar heuristicas."
            )
        if re.search(r"\bucs\b|\bcosto\s+uniforme\b|\biducs\b", norm):
            return (
                "Te refieres a la **Busqueda de Costo Uniforme (UCS)**, la cual expande el nodo de la frontera con "
                "menor costo acumulado `g(n)` siguiendo contornos de costo real (equivalente a Dijkstra hacia una meta), "
                "sin estimar nunca cuanto falta para llegar al destino."
            )
        if re.search(r"\bbidireccional\b|\bchoque\s+de\s+fronteras\b|\binterseccion\s+de\s+fronteras\b", norm):
            return (
                "Describes la **Busqueda Bidireccional**, donde dos busquedas ciegas simultaneas avanzan desde el "
                "estado inicial y hacia atras desde la meta hasta que ambas fronteras se intersectan, reduciendo "
                "el exponente de complejidad a la mitad `O(b^(d/2))`."
            )
        return (
            "Tu planteamiento describe la **Busqueda Ciega (No Informada)**: el agente trata el problema como una "
            "caja negra sin funcion heuristica `h(n)`, apoyandose solo en la definicion formal del espacio de estados, "
            "la frontera (lista abierta), el conjunto de explorados (lista cerrada) y el test de meta."
        )

    if winning_label == "Evolutiva":
        if re.search(r"\bestrategias?\s+evolutiv[ao]s?\b|\bmu\s+coma\s+lambda\b|\bmu\s+mas\s+lambda\b|\brechenberg\b|\bcma\s+es\b", norm):
            return (
                "Te refieres a las **Estrategias Evolutivas** (`(mu, lambda)`, `(mu + lambda)`, regla del quinto de exito "
                "de Rechenberg o `CMA-ES`), las cuales evolucionan vectores de numeros reales autoadaptando sus propios "
                "pasos y matrices de covarianza de mutacion."
            )
        if re.search(r"\bprogramacion\s+genetica\b|\bjohn\s+koza\b|\barboles\s+sintacticos\b|\bbloat\b|\bparsimonia\b|\bmutacion\s+de\s+subarbol\b", norm):
            return (
                "Tu texto describe la **Programacion Genetica** (John Koza), rama de la busqueda evolutiva donde cada "
                "individuo es un arbol sintactico de un programa completo que evoluciona intercambiando y mutando subarboles, "
                "controlando el hinchamiento (*bloat*) mediante presion de parsimonia."
            )
        if re.search(r"\bteorema\s+de\s+los\s+esquemas\b|\bjohn\s+holland\b|\bbloques\s+constructivos\b|\borden\s+de\s+un\s+esquema\b|\blongitud\s+de\s+definicion\b", norm):
            return (
                "Haces referencia a la base matematica de los Algoritmos Geneticos: el **Teorema de los Esquemas de John Holland** "
                "y la **Hipotesis de los Bloques Constructivos**, que explican como las plantillas cortas, de bajo orden "
                "y alto fitness se propagan exponencialmente generacion tras generacion."
            )
        if re.search(r"\bnsga\s+dos\b|\bpareto\b|\bhacinamiento\b|\bniching\b|\bmod[e]?lo\s+isla\b|\bmigracion\b|\bcoevolucion\b|\bmemetic[ao]s?\b|\bevolucion\s+diferencial\b", norm):
            return (
                "Tu planteamiento aborda tecnicas avanzadas de **Computacion Evolutiva** (como frentes de Pareto en `NSGA-II`, "
                "`Evolucion Diferencial`, `Algoritmos Memeticos`, `Modelo Isla` con migracion o `Coevolucion`), donde "
                "poblaciones cooperan o compiten preservando la diversidad genetica."
            )
        if re.search(r"\bcromosoma\b|\bgen\b|\balelo\b|\blocus\b|\bgenotipo\b|\bfenotipo\b|\bcodigo\s+gray\b|\bcruce\b|\bcrossover\b|\bmutacion\b|\bruleta\b|\btorneo\b|\bfitness\b|\baptitud\b", norm):
            return (
                "Tu texto describe los componentes fundamentales de los **Algoritmos Geneticos**: la codificacion de "
                "soluciones en **cromosomas** (genes, alelos, locus, genotipo y fenotipo), su evaluacion mediante la "
                "funcion de **aptitud (fitness)** y la evolucion mediante operadores de **seleccion, cruce y mutacion**."
            )
        return (
            "El enfoque que describes pertenece a la **Busqueda Evolutiva**: mantiene una **poblacion de soluciones "
            "candidatas** que evolucionan en paralelo inspiradas en la seleccion natural darwiniana, equilibrando "
            "la presion selectiva y la diversidad genetica a lo largo de generaciones."
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

    # Caso 1: Etiqueta Desconocido
    if winning_label == "Desconocido":
        is_greeting = bool(re.search(r"\b(?:hola|buenos\s+dias|buenas\s+tardes|buenas\s+noches|que\s+tal|como\s+estas|quien\s+eres|ayuda)\b", norm_full))
        matched_colloquial = [
            pat.replace(r"\b", "") for pat in COLLOQUIAL_TRICK_PATTERNS if re.search(pat, norm_full)
        ]
        cs_evidences = evidences.get("Desconocido", [])

        if is_greeting and len(norm_full.split()) <= 14:
            main_reason = (
                "Se asigno la etiqueta **Desconocido** porque tu mensaje es un saludo o consulta general de "
                "conversacion y aun no describe un algoritmo de busqueda."
            )
            foundation = (
                "Soy el asistente clasificador entrenado con el corpus de **420 enunciados** en 4 etiquetas "
                "(**Heuristica**, **Ciega**, **Evolutiva** y **Desconocido**). Puedes escribir cualquier concepto "
                "de busqueda o combinar los 3 algoritmos en un mismo parrafo para analizar tu caso."
            )
        elif cs_evidences:
            cs_topic = ", ".join(cs_evidences[:2])
            main_reason = (
                f"Se selecciono la etiqueta **Desconocido** porque, aunque tu enunciado trata sobre un tema de "
                f"Ciencias de la Computacion (**{cs_topic}**), no corresponde a un algoritmo de busqueda en espacios "
                f"de estados de IA bajo los paradigmas **Heuristica**, **Ciega** o **Evolutiva**."
            )
            foundation = (
                "El modelo fue entrenado especificamente para distinguir entre los algoritmos de busqueda en IA "
                "(como A*, BFS/DFS o Algoritmos Geneticos) y otros temas de informatica general (como ordenamiento "
                "de vectores, busqueda binaria, tablas hash, arboles ABB/AVL, bases de datos SQL, redes TCP/IP o "
                "sistemas operativos), clasificandolos correctamente en **Desconocido**."
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
                f"pertenece a un ambito distinto y no involucra la exploracion de estados mediante "
                f"Busqueda Ciega, Heuristica o Evolutiva."
            )
            foundation = (
                "Cuando una consulta trata sobre otros temas generales o informaticos ajenos a los tres paradigmas "
                "de busqueda en IA, el modelo la clasifica bajo **Desconocido**."
            )

        return {
            "title": label_titles["Desconocido"],
            "main_reason": main_reason,
            "multi_mention_analysis": None,
            "clues": cs_evidences if cs_evidences else ["Mensaje fuera del dominio de los 3 paradigmas de busqueda en IA"],
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
    clues_str = ", ".join(winning_clues[:4]) if winning_clues else f"las propiedades de la {label_titles[winning_label]}"

    focal_clauses = [
        c["fragment"] for c in clause_breakdown
        if winning_label in c.get("mentioned_labels", [c["detected_label"]]) and c["discourse_role"] in ("foco_principal", "afirmacion")
    ]
    focal_fragment = focal_clauses[0] if focal_clauses else user_text

    if is_question:
        main_reason = (
            f"La respuesta a tu pregunta corresponde a la etiqueta **{winning_label}** ({label_titles[winning_label]}). "
            f"Se selecciono este veredicto porque en la interrogante central (*\"{focal_fragment}\"*) preguntas especificamente "
            f"por **{clues_str}**."
        )
    elif len(mentioned_algorithms) >= 2:
        main_reason = (
            f"El veredicto es **{winning_label}** ({label_titles[winning_label]}) porque, al analizar tu mensaje completo, "
            f"la accion o concepto principal se concentra en *\"{focal_fragment}\"*, donde se "
            f"especifica el uso de **{clues_str}**."
        )
    else:
        main_reason = (
            f"Se selecciono la etiqueta **{winning_label}** ({label_titles[winning_label]}) porque tu planteamiento "
            f"hace referencia directa a **{clues_str}** dentro de *\"{focal_fragment}\"*."
        )

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
                f"Aunque tambien nombraste a {discarded_joined}, el modelo identifico que no era el metodo principal "
                f"que buscabas aplicar, dandole la victoria a **{winning_label}**."
            )

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
