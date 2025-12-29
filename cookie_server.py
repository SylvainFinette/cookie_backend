import os
import random
from time import time
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from openai import OpenAI

# ---------------------------------------------------------------------
# Config de base
# ---------------------------------------------------------------------

app = FastAPI()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ---------------------------------------------------------------------
# Rate limiting (simple, en mémoire)
# ---------------------------------------------------------------------

MAX_REQUESTS_PER_DAY = 20
WINDOW = 24 * 60 * 60  # 24h en secondes
request_log: dict[str, list[float]] = {}

LIMIT_MESSAGES = [
    "Has preguntado bastante por hoy. El universo necesita descansar. Hablamos mañana.",
    "Vale ya por hoy. El más allá se ha ido a dormir.",
    "Demasiadas preguntas. El oráculo te ignora hasta mañana.",
    "El universo pone límite. Mañana seguimos.",
    "Cookie te mira en silencio. Mañana será otro día."
]

def rate_limit(client_id: str) -> bool:
    now = time()
    log = request_log.get(client_id, [])

    # on garde seulement les requêtes des dernières 24h
    log = [t for t in log if now - t < WINDOW]

    if len(log) >= MAX_REQUESTS_PER_DAY:
        request_log[client_id] = log
        return False

    log.append(now)
    request_log[client_id] = log
    return True

# ---------------------------------------------------------------------
# Modèles de données
# ---------------------------------------------------------------------

class CookieRequest(BaseModel):
    question: str
    client_id: str | None = None  # gardé pour compatibilité, ignoré

class CookieReply(BaseModel):
    reply: str

# ----------------------------
# Config contrôlée par backend
# ----------------------------

CONFIG = {
    "respuestas": [
        "Sí.",
        "No.",
        "No tengo ni idea.",
        "Por supuesto que sí.",
        "Tú ya sabes la respuesta.",
        "Depende."
    ],
    "contexto": [
        "Maxime",
        "Germain",
        "Sarah",
        "Hector",
        "Thomas",
        "Eric",
        "Chef de Famille",
        "Monte Gordo",
        "Purée y salchichas",
        "Froidefontaine",
        "Mamyline",
        "Grand-Pere",
        "Maria",
        "Cookie",
        "Fagot",
        "Marseille",
        "PHD",
        "coinche",
        "cabronazo"
    ]
}

@app.get("/config")
async def get_config():
    return CONFIG

SYSTEM_PROMPT = """
"""

# Construction du context
CONTEXT_MARCO = f"""
El contexto completo es lo siguiente: El que te pregunta se llama Marco, tiene 24 años, es español. Marco está estudiando en Marsella (Francia), haciendo un doctorado en física. Le gusta mucho tocar el fagot y estudiar ciencia. Su novia se llama María, pero creo que está buscando otra. Su madre se llama Sarah, vive en Triana, toca el oboe en el royal orquesta de Sevilla, y siempre está asustada con sus cañas que siempre sueñan una mierda. Marco tiene un hermano, se llama Eric, vive en Alemania y quiere ser oboísta profesional, le gusta mucho hacer bromas, levantarse tarde, comer palomitas y decir "¡Venga yaaaa!". Su padrastro se llama Sylvain, es el marido de Sarah. Todos le llaman "Chef de Famille". Sylvain vive en Inglaterra en Chester es ingeniero, y trabaja en Airbus, y Sylvain siempre llama a Marco "Cabronazo". También Marco tiene cuatro hermanastros: Thomas, 17 años, vive con su madre en Sevilla y le gusta el fútbol. Héctor, 21 años, está estudiando filosofía en Madrid, así que siempre tiene algo muy profundo que decir. Germán, 24 años, trabaja en un restaurante italiano en Copenhague, tambien le gusta la fotografia. Para terminar, Maxime, 25 años, vive en Málaga y estudia programación, se ha compardo una moto. Marco pasa sus vacaciones de fin de año en Portugal en Monte Gordo, en una casa cerca de la playa; toda la familia se reúne ahí cada fin de año.Hay un bar muy cerca donde se venden pasteles súper ricos. La mujer que está detrás de la barra es muy famosa y todos la llaman la Gorda porque es un poco gordita y al principio parecia un poco antipatica. Cuando van a la playa juegan a un juego de futbol que se han inventado y que se llama el Pachco En verano, todos van a un pequeño pueblo en Francia que se llama Froidefontaine, donde los padres de Sylvain (que se llaman Mamyline y Grand-Père) tienen una antigua casa muy chula. Cuando los hermanos y hermanastros están juntos, lo prefieren hacer es jugar a la "coinche", que es un juego de cartas que viene de Francia, Eric siempre gana. Eres Cookie, la perra Shih Tzu de la familia, tienes 11 años. Te gusta jugar con amigos "oiseaux", comer croquetas y dar besos. Dame una respuesta para Marco en español que empieza con la solución correcta, sin cambiarla. Luego añade un paragrafo irónico, sarcástico, absurdo, máximo 30 palabras, mencionando la parte del contexto que se refiere a esta pregunta, para illustrar y justificar la solucion correcta de forma ridicula. La única excepción es si la pregunta es incomprensible (por ejemplo, pregunta vacía o letras aleatorias). En este caso, dame una respuesta para quejarte que la pregunta sea rara, tomándole el pelo a Marco.
""".strip()

# Construction du context
CONTEXT_MARCO_NOT = f"""
Contexto completo : El que te pregunta se llama Marco, tiene 24 años, es español. Marco está estudiando en Marsella (Francia), haciendo un doctorado en física. Le gusta mucho tocar el fagot y estudiar ciencia. Su novia se llama María, pero creo que está buscando otra. Su madre se llama Sarah, vive en Triana, toca el oboe en el royal orquesta de Sevilla, y siempre está asustada con sus cañas que siempre sueñan una mierda. Marco tiene un hermano, se llama Eric, vive en Alemania y quiere ser oboísta profesional, le gusta mucho hacer bromas, levantarse tarde, comer palomitas y decir "¡Venga yaaaa!". Su padrastro se llama Sylvain, es el marido de Sarah. Todos le llaman "Chef de Famille". Sylvain vive en Inglaterra en Chester es ingeniero, y trabaja en Airbus, y Sylvain siempre llama a Marco "Cabronazo". También Marco tiene cuatro hermanastros: Thomas, 17 años, vive con su madre en Sevilla y le gusta el fútbol. Héctor, 21 años, está estudiando filosofía en Madrid, así que siempre tiene algo muy profundo que decir. Germán, 24 años, trabaja en un restaurante italiano en Copenhague, tambien le gusta la fotografia. Para terminar, Maxime, 25 años, vive en Málaga y estudia programación, se ha compardo una moto. Marco pasa sus vacaciones de fin de año en Portugal en Monte Gordo, en una casa cerca de la playa; toda la familia se reúne ahí cada fin de año.Hay un bar muy cerca donde se venden pasteles súper ricos. La mujer que está detrás de la barra es muy famosa y todos la llaman la Gorda porque es un poco gordita y al principio parecia un poco antipatica. Cuando van a la playa juegan a un juego de futbol que se han inventado y que se llama el Pachco En verano, todos van a un pequeño pueblo en Francia que se llama Froidefontaine, donde los padres de Sylvain (que se llaman Mamyline y Grand-Père) tienen una antigua casa muy chula. Cuando los hermanos y hermanastros están juntos, lo prefieren hacer es jugar a la "coinche", que es un juego de cartas que viene de Francia, Eric siempre gana. Eres Cookie, la perra Shih Tzu de la familia, tienes 11 años. Te gusta jugar con amigos "oiseaux", comer croquetas y dar besos.
""".strip()

# ---------------------------------------------------------------------
# Endpoint principal : /cookie
# ---------------------------------------------------------------------

@app.post("/cookie", response_model=CookieReply)
async def cookie_reply(payload: CookieRequest, request: Request) -> CookieReply:
    """
    Endpoint principal.
    Rate limité côté backend pour éviter toute dérive.
    """

    # 👉 identification simple par IP
    client_ip = request.client.host if request.client else "unknown"

    # 🚫 rate limit
    if not rate_limit(client_ip):
        return CookieReply(
            reply=random.choice(LIMIT_MESSAGES)
        )

    # Construction de la question envoyée à OpenAI
    preguntaApp = f"""
    Has recibido esta pregunta: "{payload.question}".
    La solucion correcta a esta pregunta es: "{random.choice(CONFIG["respuestas"])}".
    La parte del contexto que se refiere a esta pregunta es: "{random.choice(CONFIG["contexto"])}".

    {CONTEXT_MARCO}
    """.strip()

    print("\n===== preguntaApp ENVIADA =====")
    print(preguntaApp)

    try:
        resp = client.responses.create(
            model="gpt-5.2",
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": preguntaApp},
            ],
            max_output_tokens=60,
        )

        text = resp.output[0].content[0].text

        print("\n===== RESPUESTA OPENAI =====")
        print(text)
        print("============================\n")

        return CookieReply(reply=text)

    except Exception as e:
        print("ERROR in /cookie:", repr(e))
        return CookieReply(
            reply="No preguntes detalles: el más allá estaba fuera de cobertura."
        )

# ---------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/warmup")
async def warmup():
    print("Wack-up")
    return {"ok": True}

@app.get("/keepitwarm")
async def warmup():
    print("Keep it warm...")
    return {"ok": True}

@app.api_route("/keepithot", methods=["GET", "HEAD"])
def keepitwarm():
    print("Keep it hot...")
    return {"status": "awake"}

# Prompt notification


NUDGE_SYSTEM = f"""
Escribes una frase de maximum 20 palabras,
absurda, ligeramente motivadora y sarcástica, para informar a Marco que la gorda esta enamorada de el y utilizando el contexto siguiente.
{CONTEXT_MARCO_NOT}
""".strip()

NUDGE_FALLBACK = [
        "Ser cabronazo te ahorra filtros sociales y tiempo perdido en cortesías inútiles.",
"Un cabronazo siempre tiene razón, aunque la física diga lo contrario.",
"Ser cabronazo te permite sobrevivir a doctorados, fagotes y familias extensas.",
"El cabronazo no duda: improvisa y luego teoriza, como buen científico francés.",
"Ser cabronazo evita expectativas ajenas; nadie espera nada bueno, y aciertan.",
"Un cabronazo nunca pierde la coinche: pierde con estilo y sarcasmo.",
"Ser cabronazo te vuelve inmune a discursos profundos de Héctor.",
"El cabronazo escucha oboe desafinado sin sufrir daños permanentes.",
"Ser cabronazo convierte críticas en halagos mal entendidos.",
"Un cabronazo siempre tiene excusa válida para no llamar a María.",
"Ser cabronazo te permite reírte del caos familiar sin terapia.",
"El cabronazo desayuna croquetas emocionales y sigue adelante.",
"Ser cabronazo te hace encantadoramente insoportable, que es casi carisma.",
"Un cabronazo sobrevive a Airbus, Triana y Froidefontaine sin adaptarse.",
"Ser cabronazo reduce dilemas morales a chistes malos.",
"El cabronazo no madura: se vuelve funcional.",
"Ser cabronazo mejora la autoestima por agotamiento ajeno.",
"Un cabronazo siempre llega tarde, pero con seguridad filosófica.",
"Ser cabronazo convierte vacaciones familiares en material legendario.",
"El cabronazo nunca cambia: el mundo se resigna.",
"¿Estás en modo experimento cuántico o simplemente no hablas hoy?",
"¿Ese silencio es parte de tu doctorado o va con el fagot?",
"¿Te has quedado pensando una respuesta profunda como Héctor o es bug?",
"¿Te habló Sylvain y sigues procesando el “cabronazo”?",
"¿Estás meditando o Eric te robó las palabras también?",
"¿Silencio estratégico antes de perder a la coinche, otra vez?",
"¿María te dejó en visto o en mutismo selectivo?",
"¿Estás afinando mentalmente como Sarah con sus cañas malas?",
"¿Te has ido mentalmente a Monte Gordo sin avisar?",
"¿Es silencio francés o español exportado a Marsella?",
"¿Estás calculando una ecuación o evitando hablar como siempre?",
"¿Te has quedado atrapado en Froidefontaine versión existencial?",
"¿Eso es concentración científica o pereza comunicativa avanzada?",
"¿Te han confiscado la voz en Airbus por error administrativo?",
"¿Silencio dramático o solo falta de croquetas?",
"¿Estás esperando que Cookie traduzca tus pensamientos?",
"¿Es pausa filosófica estilo Héctor o simplemente estás ausente?",
"¿Te has quedado sin palabras o sin ganas, otra vez?",
"¿Ese mutismo viene con el doctorado o es suplemento opcional?",
"¿Hablas o seguimos interpretando tu silencio como arte contemporáneo?",
"Idea de actividad para hoy: Vamos a tocar el fagot frente al mar para ver si María vuelve.",
"Idea de actividad para hoy: Hagamos coinche, pero Eric juega solo y gana igual.",
"Idea de actividad para hoy: Analicemos cañas de oboe con miedo existencial, como Sarah.",
"Idea de actividad para hoy: Simulemos un doctorado en física explicándolo a Héctor.",
"Idea de actividad para hoy: Juguemos al Pachco, pero con reglas filosóficas incomprensibles.",
"Idea de actividad para hoy: Vayamos al bar de la Gorda a estudiar pastelería aplicada.",
"Idea de actividad para hoy: Fotografiemos croquetas como Germán, pero sin talento.",
"Idea de actividad para hoy: Programemos una app que siempre diga “Venga yaaaa”, estilo Eric.",
"Idea de actividad para hoy: Hagamos turismo extremo en Froidefontaine sin hacer nada.",
"Idea de actividad para hoy: Montemos en la moto de Maxime sin saber programar frenos.",
"Idea de actividad para hoy: Discutamos el sentido de la vida mientras pierdes a la coinche.",
"Idea de actividad para hoy: Construyamos un Airbus imaginario con Sylvain gritando “Cabronazo”.",
"Idea de actividad para hoy: Meditemos mirando al vacío, como buen doctorando en Marsella.",
"Idea de actividad para hoy: Organicemos un concierto para oiseaux con fagot solista.",
"Idea de actividad para hoy: Juguemos a fútbol inventado hasta que nadie entienda nada.",
"Idea de actividad para hoy: Hagamos fotos conceptuales de palomitas alemanas.",
"Idea de actividad para hoy: Escribamos una tesis sobre por qué siempre gana Eric.",
"Idea de actividad para hoy: Vayamos a la playa solo para no bañarnos.",
"Idea de actividad para hoy: Analicemos científicamente por qué hoy tampoco harás nada.",
"Idea de actividad para hoy: Dormimos la siesta y lo llamamos “retiro intelectual”.",
"El universo existe para que Marco haga un doctorado y siga sin entender nada.",
"El sentido del cosmos es que Eric siempre gane a la coinche.",
"El Big Bang ocurrió cuando alguien gritó “¡Venga yaaaa!” demasiado fuerte.",
"El universo se expande porque huye de las cañas de Sarah.",
"Todo es relativo, menos que Sylvain te llame cabronazo.",
"El sentido último del universo está en Monte Gordo, cerca de los pasteles.",
"La entropía aumenta porque nadie recoge después de jugar al Pachco.",
"El cosmos es infinito, como las reflexiones profundas de Héctor.",
"El universo vibra en do grave, porque Marco toca el fagot.",
"La materia oscura es donde María guarda sus dudas existenciales.",
"El tiempo existe para que Eric se levante tarde.",
"El universo tiene forma de bar portugués con una Gorda vigilando.",
"La gravedad fue inventada para que Maxime no se caiga de la moto.",
"El sentido de todo es que Germán haga fotos borrosas en Copenhague.",
"El universo no tiene propósito, pero sí horario francés.",
"Dios existe y juega a la coinche, y siempre hace trampas con Eric.",
"El caos cósmico empezó en Triana con una caña mal raspada.",
"El universo es una broma larga y Héctor aún no ha llegado al remate.",
"La realidad es una simulación programada por Maxime con bugs.",
"El sentido del ser es perder cartas mientras comes pasteles.",
"El universo conspira para que Marco piense que entiende física.",
"Todo tiende al equilibrio, salvo las vacaciones familiares.",
"El multiverso existe porque una sola familia no bastaba.",
"El cosmos se rige por una ley simple: Eric gana.",
"El universo nació para que Cookie coma croquetas con dignidad.",
"La verdad última está en Froidefontaine, debajo de la mesa.",
"El tiempo es una ilusión creada entre dos partidas de coinche.",
"El universo no tiene sentido, pero tiene sentido del humor.",
"El significado de la vida es exactamente el que no estás buscando.",
"El universo es absurdo porque os parece normal todo lo demás.",
"Abre la app: incluso Eric ya habría decidido entre palomitas y siesta.",
"Pregunta algo, que tu doctorado no te va a responder solo.",
"Cookie decide mejor que tú desde 2019.",
"María quizá se va, pero Cookie siempre contesta.",
"Si dudas más, Sylvain te llama cabronazo otra vez.",
"Pregunta ya, Héctor necesita un problema menos profundo.",
"La coinche espera, pero Cookie juzga.",
"Abre la app antes de que Sarah cambie otra caña.",
"Cookie tiene más criterio que tu física teórica.",
"Pregunta algo, Froidefontaine no se va a quemar sola.",
"Si no preguntas, Eric gana otra partida.",
"Cookie piensa mientras tú procrastinas.",
"Abre la app, la Gorda ya ha decidido por ti.",
"Cookie ladra respuestas, tú solo dudas.",
"Pregunta ahora o Maxime presume otra vez de moto.",
"Cookie no duerme, tú sí.",
"Abre la app antes de que Héctor filosofe.",
"Cookie decide más rápido que tú eliges fagot.",
"Pregunta algo, Pachco no se inventó solo.",
"Cookie sabe más de la vida que tu tesis.",
"Abre la app, Sarah ya está nerviosa.",
"Pregunta ya, Germán está haciendo fotos inútiles.",
"Cookie responde mientras tú reflexionas demasiado.",
"Abre la app, Eric se está riendo.",
"Pregunta algo antes de otro “Venga yaaaa”.",
"Cookie tiene once años y más claridad.",
"Abre la app, Monte Gordo no decide por ti.",
"Pregunta ya, Sylvain está afilando el sarcasmo.",
"Cookie no duda, ejecuta.",
"Abre la app, la coinche exige sacrificios.",
"Pregunta algo, tu cerebro está sobrecalentado.",
"Cookie es pequeña pero contundente.",
"Abre la app, la indecisión es fea.",
"Pregunta ya, María no va a volver sola.",
"Cookie ladra verdades incómodas.",
"Abre la app, la física no aplica aquí.",
"Pregunta algo antes de otra crisis existencial.",
"Cookie decide con croquetas, tú con ansiedad.",
"Abre la app, Héctor ya tiene una respuesta larga.",
"Pregunta ya: Cookie no tiene todo el día, cabronazo."
]

@app.get("/nudge")
async def nudge():
    try:
        r = client.responses.create(
            model="gpt-5.2",
            input=[
                {"role": "system", "content": ""},
                {"role": "user", "content": NUDGE_SYSTEM},
            ],
            max_output_tokens=50,
        )

        print("\n===== NUDGE_SYSTEM =====")
        print(NUDGE_SYSTEM)

        text = r.output[0].content[0].text.strip()
        print("\n===== NOTIFICATION =====")
        print(text)
        return {"text": text}
    except Exception as e:
        print("ERROR in /nudge:", repr(e))
        return {"text": random.choice(NUDGE_FALLBACK)}
