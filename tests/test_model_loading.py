import sys
from types import ModuleType

from database import VectorDBManager


def test_missing_model_can_be_downloaded(monkeypatch):
    model = object()
    calls = {}

    def fake_sentence_transformer(model_name, **kwargs):
        calls["model_name"] = model_name
        calls.update(kwargs)
        return model

    sentence_transformers = ModuleType("sentence_transformers")
    sentence_transformers.SentenceTransformer = fake_sentence_transformer
    monkeypatch.setitem(sys.modules, "sentence_transformers", sentence_transformers)

    manager = VectorDBManager(client=object())

    assert manager._get_encoder() is model
    assert calls["local_files_only"] is False
