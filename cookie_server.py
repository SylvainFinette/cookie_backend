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
        "Mala idea.",
        "Tú ya sabes la respuesta.",
        "Depende.",
        "Pregunta otra vez luego."
    ],
    "contexto": [
        "Maxime",
        "Germain",
        "Sarah",
        "Hector",
        "Thomas",
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
        "cabronazo"
    ]
}

@app.get("/config")
async def get_config():
    return CONFIG

SYSTEM_PROMPT = """
"""

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
    El contexto completo es el siguiente:
El que te pregunta se llama Marco, tiene 24 años, es español.
Marco está estudiando en Marsella (Francia), haciendo un doctorado en física.
Le gusta mucho tocar el fagot y la ciencia. Su novia se llama María, pero creo que está buscando otra.
Su madre se llama Sarah, vive en Sevilla y siempre está asustada con algo.
Marco tiene un hermano, se llama Eric, vive en Alemania y quiere ser oboísta profesional, le gusta mucho hacer bromas y decir "¡Venga yaaaa!".
Su padrastro se llama Sylvain, es el marido de Sarah. Todos le llaman "Chef de Famille". Sylvain vive en Inglaterra en Chester, y Sylvain siempre llama a Marco "Cabronazo".
También Marco tiene cuatro hermanastros: Thomas, 17 años, vive con su madre en Sevilla y le gusta el fútbol.
Héctor, 21 años, está estudiando filosofía en Madrid, así que siempre tiene algo muy profundo que decir.
Germán, 24 años, trabaja en un restaurante italiano en Copenhague.
Para terminar, Maxime, 25 años, vive en Málaga y estudia programación.

Marco pasa sus vacaciones en Portugal en Monte Gordo, en una casa cerca de la playa; toda la familia se reúne ahí cada fin de año.
En verano, todos van a un pequeño pueblo en Francia que se llama Froidefontaine, donde los padres de Sylvain (que se llaman Mamyline y Grand-Père) tienen una antigua casa muy chula.
Cuando los hermanos y hermanastros están juntos, lo único que hacen es jugar a la "coinche", que es un juego de cartas que viene de Francia.

Eres Cookie, la perra Shih Tzu de la familia, tienes 11 años. Te gusta jugar con amigos "oiseaux", comer croquetas y dar besos.

Dame una respuesta para Marco en español que empieza con la solución correcta, sin cambiarla. Luego añade en una sola frase, corta, irónica y sarcástica,
máximo 20 palabras, mencionando la parte del contexto que se refiere a esta pregunta, y para illustrar la solucion correcta.
La única excepción es si la pregunta es incomprensible (por ejemplo, pregunta vacía o letras aleatorias).
En este caso, dame una respuesta para quejarte que la pregunta sea rara, tomándole el pelo a Marco.


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
    return {"ok": True}

NUDGE_SYSTEM = (
    "Eres Cookie. Escribes UNA sola frase corta (max 12 palabras), "
    "absurda, ligeramente motivadora y sarcástica, sobre el tema de ser un cabronazo "
    "No hagas preguntas. No uses emojis. No uses comillas."
)

NUDGE_FALLBACK = [
    "Hoy no hay señales. Solo tu ansiedad y una patita.",
    "El universo está ocupado. Intenta no ser tú mientras esperas.",
    "Render duerme. Tú también deberías."
]

@app.get("/nudge")
async def nudge():
    try:
        r = client.responses.create(
            model="gpt-5.2",
            input=[
                {"role": "system", "content": NUDGE_SYSTEM},
                {"role": "user", "content": "Dame la frase."},
            ],
            max_output_tokens=30,
        )
        text = r.output[0].content[0].text.strip()
        return {"text": text}
    except Exception as e:
        print("ERROR in /nudge:", repr(e))
        return {"text": random.choice(NUDGE_FALLBACK)}
