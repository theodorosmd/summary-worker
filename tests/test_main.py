from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def resumer(texte):
    return client.post("/summarize", json={"call_id": "call-1", "text": texte})


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_accident_voiture_avec_blessure():
    r = resumer("I got rear-ended on the I-10 and my neck still hurts")
    assert r.status_code == 200
    data = r.json()
    assert data["call_id"] == "call-1"
    assert data["accident_type"] == "car"
    assert data["injured"] is True
    assert data["word_count"] == 11


def test_chute_sans_blessure():
    data = resumer("I slipped in the store but I am fine").json()
    assert data["accident_type"] == "slip_and_fall"
    assert data["injured"] is False


def test_type_inconnu():
    data = resumer("I want to talk to a lawyer").json()
    assert data["accident_type"] == "other"


def test_call_id_manquant_refuse():
    r = client.post("/summarize", json={"text": "hello"})
    assert r.status_code == 422
