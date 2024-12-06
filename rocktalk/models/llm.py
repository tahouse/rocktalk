from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, List, Optional

from langchain.schema import BaseMessage
from langchain_aws import ChatBedrockConverse
from langchain_core.messages.base import BaseMessageChunk
from services.creds import get_cached_aws_credentials

from .interfaces import LLMConfig


class LLMInterface(ABC):
    @abstractmethod
    def stream(self, input: List[BaseMessage]) -> Iterator[BaseMessageChunk]: ...
    @abstractmethod
    def invoke(self, input: List[BaseMessage]) -> BaseMessage: ...
    @abstractmethod
    def update_config(self, config: Optional[LLMConfig] = None) -> None: ...
    @abstractmethod
    def get_config(self) -> LLMConfig: ...


class BedrockLLM(LLMInterface):
    _config: LLMConfig
    _llm: ChatBedrockConverse

    def __init__(self, config: Optional[LLMConfig] = None) -> None:
        if config is None:
            config = LLMConfig.get_default()
        self.update_config(config=config)

    def update_config(self, config: Optional[LLMConfig] = None) -> None:
        # debug(config)
        if config:
            self._config: LLMConfig = config.model_copy(deep=True)
        else:
            self._config = LLMConfig.get_default()
        self._update_llm()

    def get_config(self) -> LLMConfig:
        return self._config

    def _update_llm(self) -> None:
        # self._config = self._config.as_bedrock_config()
        additional_model_request_fields: Optional[Dict[str, Any]] = None
        if self._config.parameters.top_k:
            additional_model_request_fields = {"top_k": self._config.parameters.top_k}
        creds = get_cached_aws_credentials()
        self._llm = ChatBedrockConverse(
            region_name=creds.aws_region,
            model=self._config.bedrock_model_id,
            temperature=self._config.parameters.temperature,
            max_tokens=self._config.parameters.max_output_tokens,
            stop=self._config.stop_sequences,
            top_p=self._config.parameters.top_p,
            additional_model_request_fields=additional_model_request_fields,
            aws_access_key_id=creds.aws_access_key_id,
            aws_secret_access_key=creds.aws_secret_access_key,
            aws_session_token=creds.aws_session_token,
        )

    def stream(self, input) -> Iterator[BaseMessageChunk]:
        return self._llm.stream(input=input)

    def invoke(self, input) -> BaseMessage:
        return self._llm.invoke(input=input)
