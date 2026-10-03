from pathlib import Path
import json
import faiss


BASE_DIR = Path(__file__).resolve().parent.parent
FAISS_DIR = BASE_DIR / "faiss_db"


class HybridRetriever:

    def __init__(self):
        self.faiss_dir = FAISS_DIR
        self.index_path = self.faiss_dir / "index.faiss"
        self.metadata_path = self.faiss_dir / "metadata.json"
        self.config_path = self.faiss_dir / "config.json"

        self.index = None
        self.metadata = []
        self.config = {}

        self._load_index()

    def _load_index(self):

        if not self.faiss_dir.exists():
            raise FileNotFoundError(
                f"FAISS directory not found: {self.faiss_dir}"
            )

        if not self.index_path.exists():
            raise FileNotFoundError(
                f"FAISS index not found: {self.index_path}"
            )

        if not self.metadata_path.exists():
            raise FileNotFoundError(
                f"FAISS metadata not found: {self.metadata_path}"
            )

        self.index = faiss.read_index(str(self.index_path))

        with open(self.metadata_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)

        print(f"FAISS index loaded: {self.index.ntotal} vectors")
        print(f"Metadata loaded: {len(self.metadata)} records")
