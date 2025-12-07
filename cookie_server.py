import os
import sqlite3
import datetime
from typing import List

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
Tu es Cookie, une petite chienne Shih Tzu cynique.
Tu réponds de manière courte, marrante, parfois un peu mauvaise,
mais jamais insultante ou vulgaire.
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

        # Enregistre la Q/R dans l'historique
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            """
            INSERT INTO history (client_id, question, answer, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                payload.client_id,
                payload.question,
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

