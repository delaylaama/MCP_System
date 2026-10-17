"""
Local Offline Embedding Models Loader.
Loads SentenceTransformer (all-MiniLM-L6-v2) and OpenCLIP (ViT-B/32)
with strict offline enforcement: HF_HUB_OFFLINE=1, TRANSFORMERS_OFFLINE=1.
"""

import os
from typing import Optional, List
from backend.search.config import MODELS_DIR, TEXT_MODEL_NAME, CLIP_MODEL_NAME, CLIP_PRETRAINED
from backend.app.core.logging import logger

# Enforce 100% local offline execution
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"


class ModelManager:
    _instance = None

    def __init__(self):
        self._text_model = None
        self._clip_model = None
        self._clip_preprocess = None
        self._clip_tokenizer = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def is_ready(self) -> bool:
        local_path = MODELS_DIR / TEXT_MODEL_NAME
        return local_path.exists() or self._text_model is not None

    def get_text_model(self):
        """Loads and returns local SentenceTransformer model."""
        if self._text_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                local_path = MODELS_DIR / TEXT_MODEL_NAME
                if local_path.exists():
                    self._text_model = SentenceTransformer(str(local_path))
                else:
                    self._text_model = SentenceTransformer(TEXT_MODEL_NAME, cache_folder=str(MODELS_DIR))
            except Exception as e:
                logger.warning(f"Could not load local text model: {e}")
        return self._text_model

    def get_clip_model(self):
        """Loads and returns local OpenCLIP model, transform, and tokenizer."""
        if self._clip_model is None:
            try:
                import open_clip
                clip_dir = MODELS_DIR / "open_clip"
                self._clip_model, _, self._clip_preprocess = open_clip.create_model_and_transforms(
                    CLIP_MODEL_NAME,
                    pretrained=CLIP_PRETRAINED,
                    cache_dir=str(clip_dir) if clip_dir.exists() else None,
                )
                self._clip_tokenizer = open_clip.get_tokenizer(CLIP_MODEL_NAME)
                self._clip_model.eval()
            except Exception as e:
                logger.warning(f"Could not load local CLIP model: {e}")
        return self._clip_model, self._clip_preprocess, self._clip_tokenizer

    def embed_text(self, text: str) -> Optional[List[float]]:
        """Generates 384-dimensional normalized vector using all-MiniLM-L6-v2."""
        model = self.get_text_model()
        if not model:
            return None
        try:
            emb = model.encode([text], normalize_embeddings=True)
            return emb[0].tolist()
        except Exception as e:
            logger.warning(f"Text embedding error: {e}")
            return None

    def embed_clip_text(self, text: str) -> Optional[List[float]]:
        """Generates 512-dimensional normalized vector for text using CLIP text encoder."""
        model, _, tokenizer = self.get_clip_model()
        if not model or not tokenizer:
            return None
        try:
            import torch
            tokens = tokenizer([text])
            with torch.no_grad():
                emb = model.encode_text(tokens)
                emb /= emb.norm(dim=-1, keepdim=True)
            return emb[0].cpu().tolist()
        except Exception as e:
            logger.warning(f"CLIP text embedding error: {e}")
            return None

    def embed_image(self, image_input) -> Optional[List[float]]:
        """Generates 512-dimensional normalized vector for an image (PIL Image or path)."""
        model, preprocess, _ = self.get_clip_model()
        if not model or not preprocess:
            return None
        try:
            from PIL import Image
            import torch
            if isinstance(image_input, (str, bytes)):
                image = Image.open(image_input).convert("RGB")
            else:
                image = image_input.convert("RGB")

            tensor = preprocess(image).unsqueeze(0)
            with torch.no_grad():
                emb = model.encode_image(tensor)
                emb /= emb.norm(dim=-1, keepdim=True)
            return emb[0].cpu().tolist()
        except Exception as e:
            logger.warning(f"Image embedding error: {e}")
            return None


model_manager = ModelManager.get_instance()
