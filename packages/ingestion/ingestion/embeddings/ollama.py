import httpx
from typing import List
import time

class OllamaEmbedder:
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "nomic-embed-text"):
        self.base_url = base_url.rstrip("/")
        self.model = model
        
    def ensure_model_pulled(self):
        """Checks if the model exists locally, and pulls it if not."""
        print(f"Ensuring model '{self.model}' is pulled from Ollama...")
        # Get list of models
        try:
            resp = httpx.get(f"{self.base_url}/api/tags")
            resp.raise_for_status()
            models = resp.json().get("models", [])
            model_names = [m["name"] for m in models]
            
            # Simple check if model exists (Ollama adds :latest sometimes)
            if not any(self.model in name for name in model_names):
                print(f"Model '{self.model}' not found locally. Pulling...")
                # Pull model (this could take a while, so we increase timeout)
                pull_resp = httpx.post(
                    f"{self.base_url}/api/pull", 
                    json={"name": self.model, "stream": False},
                    timeout=300.0
                )
                pull_resp.raise_for_status()
                print(f"Model '{self.model}' pulled successfully.")
            else:
                print(f"Model '{self.model}' is already available.")
        except httpx.RequestError as e:
            print(f"Failed to connect to Ollama at {self.base_url}: {e}")
            raise

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embeds a list of texts using the configured Ollama model."""
        embeddings = []
        with httpx.Client(timeout=60.0) as client:
            for text in texts:
                resp = client.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": self.model, "prompt": text}
                )
                resp.raise_for_status()
                embeddings.append(resp.json()["embedding"])
        return embeddings
