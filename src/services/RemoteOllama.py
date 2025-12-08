import base64
from langchain_ollama import OllamaLLM

class RemoteOllama:
    """
    A wrapper for connecting to a secure, self-hosted Ollama instance via Caddy.
    """
    def __init__(self, base_url, username, password, model="llama3", **kwargs):
        """
        Args:
            base_url (str): The full URL (e.g., "https://ollama.yourdomain.com")
            username (str): The Caddy basic auth username
            password (str): The Caddy basic auth password
            model (str): The Ollama model to use (default: "llama3")
            **kwargs: Additional arguments for OllamaLLM (temperature, etc.)
        """
        # 1. Sanitize URL
        # Remove trailing slashes and accidental '/api' suffixes to prevent 404s
        self.base_url = base_url.rstrip('/').replace("/api", "")
        self.model = model
        
        # 2. Generate Auth Header
        # We do the encoding manually to ensure no hidden chars break the handshake.
        credentials = f"{username}:{password}"
        auth_b64 = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
        
        self.headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/json"
        }

        # 3. Initialize LangChain
        # FIX: We pass headers in 'client_kwargs' as well to ensure they stick
        self.llm = OllamaLLM(
            base_url=self.base_url,
            model=self.model,
            headers=self.headers,
            client_kwargs={"headers": self.headers},
            **kwargs
        )

    def invoke(self, prompt):
        """Directly invokes the model with a string prompt."""
        return self.llm.invoke(prompt)

    def get_llm(self):
        """Returns the raw LangChain LLM object for use in Chains/Agents."""
        return self.llm

llm = RemoteOllama(
    base_url="http://ollama.bencombs.art",
    username="admin",
    password="011iv3r0329!",
    model="mannix/llama3.1-8b-lexi:latest"
).get_llm()