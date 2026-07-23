"""
Base agent class for the multi-agent pipeline.
"""

import time
import os
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from datetime import datetime

from app.models import AgentTrace, AgentType
from app.rag.data_loader import DataLoader
from app.rag.embeddings import EmbeddingService


class BaseAgent(ABC):
    """Base class for all agents in the pipeline."""

    def __init__(self, agent_type: AgentType, data_loader: DataLoader, 
                 embedding_service: Optional[EmbeddingService] = None):
        self.agent_type = agent_type
        self.data_loader = data_loader
        self.embeddings = embedding_service
        self.provider = os.getenv("AI_PROVIDER", "mock")
        self.openai_client = None
        self._init_openai()

    def _init_openai(self):
        """Initialize OpenAI client if available."""
        if self.provider == "openai":
            try:
                from openai import OpenAI
                api_key = os.getenv("OPENAI_API_KEY", "")
                if api_key:
                    self.openai_client = OpenAI(api_key=api_key)
            except ImportError:
                pass

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Call an LLM for text generation. Falls back to rule-based for mock."""
        if self.provider == "openai" and self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model=os.getenv("OPENAI_MODEL", "gpt-4"),
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=500
                )
                return response.choices[0].message.content
            except Exception:
                return self._rule_based_response(user_prompt)
        elif self.provider == "groq":
            try:
                from openai import OpenAI as GroqClient
                client = GroqClient(
                    base_url="https://api.groq.com/openai/v1",
                    api_key=os.getenv("GROQ_API_KEY", "")
                )
                response = client.chat.completions.create(
                    model=os.getenv("GROQ_MODEL", "llama3-70b-8192"),
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3
                )
                return response.choices[0].message.content
            except Exception:
                return self._rule_based_response(user_prompt)
        elif self.provider == "openrouter":
            try:
                from openai import OpenAI as ORClient
                client = ORClient(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=os.getenv("OPENROUTER_API_KEY", "")
                )
                response = client.chat.completions.create(
                    model=os.getenv("OPENROUTER_MODEL", "anthropic/claude-3-opus"),
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3
                )
                return response.choices[0].message.content
            except Exception:
                return self._rule_based_response(user_prompt)
        elif self.provider == "ollama":
            try:
                import httpx
                base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
                model = os.getenv("OLLAMA_MODEL", "llama3")
                response = httpx.post(
                    f"{base_url}/api/chat",
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "stream": False
                    },
                    timeout=30
                )
                return response.json()["message"]["content"]
            except Exception:
                return self._rule_based_response(user_prompt)
        else:
            return self._rule_based_response(user_prompt)

    def _rule_based_response(self, prompt: str) -> str:
        """Fallback rule-based response for mock mode."""
        return self._mock_agent_response(prompt)

    @abstractmethod
    def _mock_agent_response(self, prompt: str) -> str:
        """Mock response for testing without LLM."""
        pass

    def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> AgentTrace:
        """Execute the agent and return a trace."""
        start_time = time.time()
        trace = AgentTrace(
            agent=self.agent_type,
            status="running",
            input=str(input_data),
            processingTimeMs=0
        )

        try:
            result = self.process(input_data, context)
            trace.output = str(result)
            trace.status = "completed"
            trace.evidence = self._get_evidence()
        except Exception as e:
            trace.status = "failed"
            trace.error = str(e)
            trace.output = f"Error: {str(e)}"

        trace.processingTimeMs = int((time.time() - start_time) * 1000)
        return trace

    @abstractmethod
    def process(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Process input and return output. Implemented by each agent."""
        pass

    def _get_evidence(self) -> List[Dict[str, Any]]:
        """Get evidence collected by this agent."""
        return []

