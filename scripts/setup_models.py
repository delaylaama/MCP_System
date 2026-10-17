"""
One-Time Local Model Download and Offline Verification Script.
Downloads:
1. all-MiniLM-L6-v2 (Text embeddings - SentenceTransformers)
2. ViT-B/32 via open_clip (Multimodal Image + Text embeddings)

Stores them locally in %APPDATA%/MCP Drivers/models/ and validates loading
in strict offline mode (HF_HUB_OFFLINE=1, TRANSFORMERS_OFFLINE=1).
"""

import os
import sys
from pathlib import Path

# Force UTF-8 stdout encoding on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add project root to sys.path
root_dir = Path(__file__).parent.parent.resolve()
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.search.config import MODELS_DIR, TEXT_MODEL_NAME, CLIP_MODEL_NAME, CLIP_PRETRAINED


def download_and_verify():
    print("=" * 60)
    print("Starting One-Time Local Model Setup for MCP Drivers...")
    print(f"Target Directory: {MODELS_DIR}")
    print("=" * 60)

    # 1. Download Sentence Transformer model
    print(f"\n[1/2] Downloading Text Embedding Model: {TEXT_MODEL_NAME}...")
    try:
        from sentence_transformers import SentenceTransformer
        text_model_path = MODELS_DIR / TEXT_MODEL_NAME
        
        # Download and save to target directory
        model = SentenceTransformer(TEXT_MODEL_NAME, cache_folder=str(MODELS_DIR))
        model.save(str(text_model_path))
        print(f"[SUCCESS] Downloaded and saved {TEXT_MODEL_NAME} to {text_model_path}")
    except Exception as e:
        print(f"[FAIL] Failed to download {TEXT_MODEL_NAME}: {e}")
        sys.exit(1)

    # 2. Download CLIP model via open_clip
    print(f"\n[2/2] Downloading Vision & Multimodal Model: {CLIP_MODEL_NAME} ({CLIP_PRETRAINED})...")
    try:
        import open_clip
        clip_cache_dir = MODELS_DIR / "open_clip"
        clip_cache_dir.mkdir(parents=True, exist_ok=True)
        
        clip_model, _, preprocess = open_clip.create_model_and_transforms(
            CLIP_MODEL_NAME,
            pretrained=CLIP_PRETRAINED,
            cache_dir=str(clip_cache_dir),
        )
        tokenizer = open_clip.get_tokenizer(CLIP_MODEL_NAME)
        print(f"[SUCCESS] Downloaded {CLIP_MODEL_NAME} ({CLIP_PRETRAINED}) to {clip_cache_dir}")
    except Exception as e:
        print(f"[FAIL] Failed to download {CLIP_MODEL_NAME}: {e}")
        sys.exit(1)

    # 3. Test Offline Verification
    print("\n" + "=" * 60)
    print("Enabling strict offline mode (HF_HUB_OFFLINE=1, TRANSFORMERS_OFFLINE=1)...")
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"

    print("Verifying text model loading in offline mode...")
    try:
        offline_text_model = SentenceTransformer(str(text_model_path))
        test_emb = offline_text_model.encode(["Test embedding query"])
        assert len(test_emb) == 1 and len(test_emb[0]) == 384
        print("[SUCCESS] Text model verified working in offline mode (384-dimensional vector)!")
    except Exception as e:
        print(f"[FAIL] Offline text model verification failed: {e}")
        sys.exit(1)

    print("Verifying CLIP model loading in offline mode...")
    try:
        offline_clip, _, offline_preprocess = open_clip.create_model_and_transforms(
            CLIP_MODEL_NAME,
            pretrained=CLIP_PRETRAINED,
            cache_dir=str(clip_cache_dir),
        )
        test_tokens = tokenizer(["a photo of a leaf"])
        test_clip_emb = offline_clip.encode_text(test_tokens)
        assert test_clip_emb.shape[-1] == 512
        print("[SUCCESS] CLIP model verified working in offline mode (512-dimensional vector)!")
    except Exception as e:
        print(f"[FAIL] Offline CLIP model verification failed: {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("All AI Search models downloaded and verified 100% offline!")
    print("=" * 60)


if __name__ == "__main__":
    download_and_verify()
