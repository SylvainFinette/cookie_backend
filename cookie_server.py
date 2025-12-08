import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI
import random


# ---------------------------------------------------------------------
# Config de base
# ---------------------------------------------------------------------

app = FastAPI()

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ---------------------------------------------------------------------
# Modèles de données
# ---------------------------------------------------------------------


class CookieRequest(BaseModel):
    question: str
    # gardé pour compatibilité avec l'app, mais ignoré côté serveur
    client_id: str | None = None


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
        "PHD"
    ]
}

@app.get("/config")
async def get_config():
    """
    Renvoie la configuration dynamique utilisée par l'app.
    Cela permet de changer les listes sans recompiler l'APK.
    """
    return CONFIG


SYSTEM_PROMPT = """
"""

# ---------------------------------------------------------------------
# Endpoint principal : /cookie
# ---------------------------------------------------------------------


@app.post("/cookie", response_model=CookieReply)
async def cookie_reply(payload: CookieRequest) -> CookieReply:
    """
    Reçoit la question déjà formatée par l'app (avec la "respuesta correcta" et el contexto),
    envoie tout ça à OpenAI, et renvoie juste la phrase de Cookie.
    Aucun stockage, aucune base, aucun GitHub. Zen.
    """
    # On fabrique ici la frase "preguntaApp"
    preguntaApp = f"""
    Has recibido esta pregunta: "{payload.question}".

    La respuesta correcta a esta pregunta es: "{random.choice(CONFIG["respuestas"])}".

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

Dame una respuesta para Marco en español que reformule la solución correcta, en una sola frase, corta, irónica y sarcástica.
Máximo 10-12 palabras, siempre mencionando la parte del contexto que se refiere a esta pregunta.
La única excepción es si la pregunta es incomprensible (por ejemplo, pregunta vacía o letras aleatorias).
En este caso, dame una respuesta para quejarte que la pregunta sea rara, tomándole el pelo a Marco, porque ¡tú tienes otra cosa que hacer!

    """.strip()

    # 🔥 LOG que tu peux voir dans Render
    print("\n\n===== preguntaApp ENVOYÉE À OPENAI =====")
    print(preguntaApp)

    try:
        resp = client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": preguntaApp},
            ],
            max_output_tokens=60,
        )

        text = resp.output[0].content[0].text


        # 🔥 LOG que tu peux voir dans Render
        print("\n\n===== text RECU DE OPENAI =====")
        print(text)
        print("========================================\n")


        return CookieReply(reply=text)

    except Exception as e:
        print("ERROR in /cookie:", repr(e))
        raise HTTPException(status_code=500, detail="Cookie ha tenido un mal día")


# Petit endpoint santé si tu veux tester vite fait
@app.get("/health")
async def health():
    return {"status": "ok"}

