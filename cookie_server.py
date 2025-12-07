import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

class Question(BaseModel):
    question: str

SYSTEM_PROMPT = """
Bienvenido a la app de cookie.
"""

@app.post("/cookie")
async def cookie_reply(payload: Question):
    try:
        resp = client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": payload.question},
            ],
            max_output_tokens=60,
        )

        text = resp.output[0].content[0].text
        return {"reply": text}

    except Exception as e:
        # Pour voir ce qui se passe dans les logs Railway
        print("ERROR in /cookie:", repr(e))
        raise HTTPException(status_code=500, detail="Cookie ha tenido un mal día")

