import sys
from queue import Queue
from types import ModuleType

from database import VectorDBManager
from model_download import MODEL_DOWNLOAD_ALLOW_PATTERNS, download_embedding_model


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


def test_download_progress_does_not_require_tqdm_description(monkeypatch):
    calls = {}

    class FakeTqdm:
        def __init__(self, *args, **kwargs):
            self.n = kwargs.get("initial", 0)
            self.total = kwargs.get("total")

        def update(self, amount=1):
            self.n += amount
            return True

    def fake_snapshot_download(repo_id, **kwargs):
        calls["repo_id"] = repo_id
        calls.update(kwargs)
        progress_bar = kwargs["tqdm_class"](
            desc="Downloading bytes",
            unit="B",
            total=10,
        )
        progress_bar.update(3)

    huggingface_hub = ModuleType("huggingface_hub")
    huggingface_hub.snapshot_download = fake_snapshot_download
    huggingface_hub_utils = ModuleType("huggingface_hub.utils")
    huggingface_hub_tqdm = ModuleType("huggingface_hub.utils.tqdm")
    huggingface_hub_tqdm.tqdm = FakeTqdm
    monkeypatch.setitem(sys.modules, "huggingface_hub", huggingface_hub)
    monkeypatch.setitem(sys.modules, "huggingface_hub.utils", huggingface_hub_utils)
    monkeypatch.setitem(sys.modules, "huggingface_hub.utils.tqdm", huggingface_hub_tqdm)

    progress = Queue()
    download_embedding_model(progress)

    assert progress.get_nowait() == ("Downloading bytes", 3, 10, "B")
    assert calls["allow_patterns"] == MODEL_DOWNLOAD_ALLOW_PATTERNS
    assert calls["max_workers"] == 1


def test_download_patterns_skip_optional_model_backends():
    from huggingface_hub.utils import filter_repo_objects

    files = [
        "config.json",
        "model.safetensors",
        "onnx/model.onnx",
        "openvino/openvino_model.bin",
        "tf_model.h5",
    ]

    selected = list(
        filter_repo_objects(items=files, allow_patterns=MODEL_DOWNLOAD_ALLOW_PATTERNS)
    )

    assert selected == ["config.json", "model.safetensors"]
