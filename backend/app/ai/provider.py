from abc import ABC, abstractmethod
from typing import Any, Dict


class AIProvider(ABC):
    """
    Abstract interface for TARK's AI reasoning providers.

    TARK agents communicate with this interface rather than
    directly depending on a specific AI provider.
    """

    @abstractmethod
    def generate_json(
        self,
        prompt: str,
    ) -> Dict[str, Any]:
        """
        Send a prompt to an AI provider and return validated JSON.

        Each provider implementation is responsible for calling
        its API and converting the response into a Python dictionary.
        """

        raise NotImplementedError