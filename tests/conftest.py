import pytest

import main


@pytest.fixture(autouse=True)
def sans_llm(monkeypatch):
    def llm_en_panne(texte):
        raise RuntimeError("LLM coupe pendant les tests")

    monkeypatch.setattr(main, "extract_with_llm", llm_en_panne)
