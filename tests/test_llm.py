from fastapi.testclient import TestClient

import main
from main import Extraction, app

client = TestClient(app)


def resumer(texte):
    return client.post("/summarize", json={"call_id": "call-1", "text": texte})


def test_llm_utilise_quand_disponible(monkeypatch):
    def faux_llm(texte):
        return Extraction(injured=False, accident_type="other")

    monkeypatch.setattr(main, "extract_with_llm", faux_llm)
    data = resumer("I was not hurt, I just want to know my rights").json()
    assert data["method"] == "llm"
    assert data["injured"] is False


def test_llm_en_panne_bascule_sur_mots_cles():
    r = resumer("I got rear-ended and my neck hurts")
    assert r.status_code == 200
    data = r.json()
    assert data["method"] == "keywords"
    assert data["accident_type"] == "car"
