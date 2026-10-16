import logging
import os
from typing import Literal

import litellm
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, Field

load_dotenv()

app = FastAPI(title="summary-worker")

AccidentType = Literal["car", "slip_and_fall", "work", "other"]

MOTS_BLESSURE = ["hurt", "injured", "pain", "hospital", "broke"]
MOTS_ACCIDENT: dict[AccidentType, list[str]] = {
    "car": ["car", "truck", "rear-ended", "crash"],
    "slip_and_fall": ["slipped", "fell", "wet floor"],
    "work": ["at work", "job site", "my boss"],
}

PROMPT = (
    "You read phone call transcripts for a US personal injury law firm. "
    "Answer only with JSON, no other text: "
    '{"injured": true or false, '
    '"accident_type": "car" or "slip_and_fall" or "work" or "other"}. '
    "injured is true only if the caller says they were physically hurt."
)


class Transcript(BaseModel):
    call_id: str
    text: str = Field(min_length=1)


class Extraction(BaseModel):
    injured: bool
    accident_type: AccidentType


class Summary(BaseModel):
    call_id: str
    word_count: int
    injured: bool
    accident_type: AccidentType
    method: str


def extract_with_keywords(texte: str) -> Extraction:
    texte = texte.lower()
    injured = any(mot in texte for mot in MOTS_BLESSURE)
    accident_type: AccidentType = "other"
    for type_accident, mots in MOTS_ACCIDENT.items():
        if any(mot in texte for mot in mots):
            accident_type = type_accident
            break
    return Extraction(injured=injured, accident_type=accident_type)


def extract_with_llm(texte: str) -> Extraction:
    reponse = litellm.completion(
        model=os.environ["LLM_MODEL"],
        messages=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": texte},
        ],
        timeout=20,
    )
    contenu = reponse.choices[0].message.content
    json_brut = contenu[contenu.find("{") : contenu.rfind("}") + 1]
    return Extraction.model_validate_json(json_brut)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/summarize")
def summarize(t: Transcript) -> Summary:
    try:
        extraction = extract_with_llm(t.text)
        method = "llm"
    except Exception as erreur:
        logging.warning("LLM indisponible, mots-cles utilises : %r", erreur)
        extraction = extract_with_keywords(t.text)
        method = "keywords"
    return Summary(
        call_id=t.call_id,
        word_count=len(t.text.split()),
        injured=extraction.injured,
        accident_type=extraction.accident_type,
        method=method,
    )
