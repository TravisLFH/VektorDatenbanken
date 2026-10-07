"""Hugging Face embedding-model download with progress reporting."""

from __future__ import annotations

import io
import logging
from pathlib import Path
from queue import Queue

from config import CONFIG
from errors import EmbeddingModelError

logger = logging.getLogger(__name__)

MODEL_DOWNLOAD_ALLOW_PATTERNS = (
    "*.json",
    "*.safetensors",
    "*.model",
    "*.txt",
    "*.vocab",
    "*.merges",
    "*.tiktoken",
)


def download_embedding_model(progress: Queue[tuple[str, float, float | None, str]]) -> None:
    """Prefetch PyTorch model and tokenizer files, not optional backend exports."""
    try:
        from huggingface_hub import snapshot_download
        from huggingface_hub.utils.tqdm import tqdm

        class StreamlitProgress(tqdm):
            def __init__(self, *args, **kwargs):
                self._progress_description = kwargs.get("desc") or "Modelldatei"
                self._progress_unit = kwargs.get("unit") or ""
                kwargs["file"] = io.StringIO()
                super().__init__(*args, **kwargs)

            def update(self, n: int = 1) -> bool:
                updated = super().update(n)
                progress.put(
                    (
                        self._progress_description,
                        getattr(self, "n", 0),
                        getattr(self, "total", None),
                        self._progress_unit,
                    )
                )
                return updated

        model_name = CONFIG.embedding_model
        repo_id = (
            model_name
            if "/" in model_name or Path(model_name).is_dir()
            else f"sentence-transformers/{model_name}"
        )
        snapshot_download(
            repo_id,
            max_workers=1,
            allow_patterns=MODEL_DOWNLOAD_ALLOW_PATTERNS,
            tqdm_class=StreamlitProgress,
        )
    except Exception as exc:
        logger.exception("Embedding-Modell konnte nicht heruntergeladen werden.")
        raise EmbeddingModelError(
            "Das Embedding-Modell konnte weder aus dem lokalen Hugging-Face-Cache "
            "geladen noch aus dem Internet heruntergeladen werden."
        ) from exc
