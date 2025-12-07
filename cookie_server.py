import os
import sqlite3
import datetime
from typing import List
import re


from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI

# ---------------------------------------------------------------------
# Config de base
# ---------------------------------------------------------------------

app = FastAPI()

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

DB_PATH = "history.db"


def init_db() -> None:
    """Création de la table d'historique si elle n'existe pas."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id  TEXT,
            question   TEXT,
            answer     TEXT,
            created_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()


init_db()

# ---------------------------------------------------------------------
# Modèles de données
# ---------------------------------------------------------------------


class CookieRequest(BaseModel):
    question: str
    client_id: str | None = None


class CookieReply(BaseModel):
    reply: str


class HistoryItem(BaseModel):
    question: str
    answer: str
    created_at: str


SYSTEM_PROMPT = """
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
"""

# ---------------------------------------------------------------------
# Endpoint principal : /cookie
# ---------------------------------------------------------------------


@app.post("/cookie", response_model=CookieReply)
async def cookie_reply(payload: CookieRequest) -> CookieReply:
    try:
        resp = client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": payload.question},
            ],
            max_output_tokens=60,
        )

        # Récupère le texte renvoyé par l'API OpenAI
        text = resp.output[0].content[0].text

        raw_q = payload.question
        match = re.search(r'Has recibido esta pregunta:\s*"([^"]+)"', raw_q)
        if match:
            real_question = match.group(1)
        else:
            # fallback si jamais la regex ne trouve rien
            real_question = raw_q.strip()

        # Enregistre la Q/R dans l'historique
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            """
            INSERT INTO history (client_id, question, answer, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                payload.client_id,
                real_question,
                text,
                datetime.datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
        conn.close()

        return CookieReply(reply=text)

    except Exception as e:
        print("ERROR in /cookie:", repr(e))
        raise HTTPException(status_code=500, detail="Cookie ha tenido un mal día")


@app.delete("/history/clear_all")
def clear_all_history():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM history")
    conn.commit()
    conn.close()
    return {"status": "ok", "message": "History cleared"}

# ---------------------------------------------------------------------
# Endpoint historique : /history
# ---------------------------------------------------------------------


@app.get("/history", response_model=List[HistoryItem])
def get_history(client_id: str | None = None, limit: int = 50) -> List[HistoryItem]:
    """
    Renvoie l'historique des questions/réponses.

    - Si client_id est fourni : historique pour ce client.
    - Sinon : historique global (pour debug).
    """
    conn = sqlite3.connect(DB_PATH)

    if client_id:
        rows = conn.execute(
            """
            SELECT question, answer, created_at
            FROM history
            WHERE client_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (client_id, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT question, answer, created_at
            FROM history
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    conn.close()

    return [
        HistoryItem(question=q, answer=a, created_at=t)
        for (q, a, t) in rows
    ]

