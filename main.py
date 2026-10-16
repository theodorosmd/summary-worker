from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="summary-worker")

AccidentType = Literal["car", "slip_and_fall", "work", "other"]

MOTS_BLESSURE = ["hurt", "injured", "pain", "hospital", "broke"]
MOTS_ACCIDENT: dict[AccidentType, list[str]] = {
    "car": ["car", "truck", "rear-ended", "crash"],
    "slip_and_fall": ["slipped", "fell", "wet floor"],
    "work": ["at work", "job site", "my boss"],
}


class Transcript(BaseModel):
    call_id: str
    text: str = Field(min_length=1)


class Summary(BaseModel):
    call_id: str
    word_count: int
    injured: bool
    accident_type: AccidentType
    method: str


def detect_injured(texte: str) -> bool:
    return any(mot in texte for mot in MOTS_BLESSURE)


def detect_accident_type(texte: str) -> AccidentType:
    for type_accident, mots in MOTS_ACCIDENT.items():
        if any(mot in texte for mot in mots):
            return type_accident
    return "other"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/summarize")
def summarize(t: Transcript) -> Summary:
    texte = t.text.lower()
    return Summary(
        call_id=t.call_id,
        word_count=len(t.text.split()),
        injured=detect_injured(texte),
        accident_type=detect_accident_type(texte),
        method="keywords",
    )
