import base64
import httpx

from abc import ABC, abstractmethod
from pydantic import BaseModel
from pydantic_ai import (
    Agent,
    ImageUrl,
    BinaryContent,
    DocumentUrl,
    ModelSettings,
    Tool,
    BinaryImage,
)
from pydantic_ai.builtin_tools import AbstractBuiltinTool
from typing import Optional, List, Union

from src.utils import setup_logger


class BaseAgent(ABC):
    """
    abstract base class for all agents

    @methods:
    - prepare_images(images): prepares images for the agent by converting them to appropriate format
    - prepare_documents(document_urls): prepares document urls for the agent
    - invoke(query, images=None, document_urls=None): The main logic for running the agent with specified query and images

    @abstractmethods:
    - execute(state):
        reads from the state to get context, and runs the agent.
        this func is for langgraph
    """

    STATUS_CONSTANTS = [
        "COMPLETE",
        "IN_PROGRESS",
        "FAILED",
        "NEED_HUMAN_INPUT",
        "HUMAN_INPUT_RECEIVED",
    ]

    def __init__(
        self,
        provider: str,
        model_name: str,
        system_prompt: Optional[str] = "",
        instructions: Optional[str] = "",
        tools: Optional[List[Tool]] = [],
        builtin_tools: Optional[List[AbstractBuiltinTool]] = [],
        output_type: Union[type, BaseModel] = str,
        model_settings: Optional[dict] = {},
    ):
        self.logger = setup_logger(f"[{self.__class__.__name__}]")
        self.model_str = f"{provider}:{model_name}"
        self.agent = Agent(
            self.model_str,
            system_prompt=system_prompt,
            instructions=instructions,
            tools=tools,
            builtin_tools=builtin_tools,
            output_type=output_type,
            model_settings=ModelSettings(**model_settings),
        )

    def __repr__(self):
        return f"<{self.__class__.__name__}, model={self.model_str}>"

    def format_chat_history(self, chat_history: str) -> str:
        return f"Chat History:\n{chat_history}\n\n"

    def add_user_message(self, user_message: str) -> str:
        return f"User: {user_message}\n\n"

    def add_agent_message(self, agent_message: str) -> str:
        return f"Agent: {agent_message}\n\n"

    def format_user_and_agent_messages(
        self,
        user_message: str,
        agent_message: str,
    ) -> str:
        return self.add_user_message(user_message) + self.add_agent_message(
            agent_message
        )

    def _is_base64(self, s: str) -> bool:
        """helper method to check if string is valid base64"""
        try:
            return base64.b64encode(base64.b64decode(s)).decode() == s
        except Exception:
            return False

    def prepare_images(self, images: List[str]):
        """
        prepares images for the agent by converting them to appropriate format
        handles urls, local file paths, and base64 encoded images
        """
        prepared_images = []

        for image in images:
            # check if it's a base64 data url
            if image.startswith("data:image/"):
                try:
                    # extract media type and base64 data
                    header, base64_data = image.split(",", 1)
                    media_type = header.split(":")[1].split(";")[0]
                    image_data = base64.b64decode(base64_data)
                    prepared_images.append(
                        BinaryContent(data=image_data, media_type=media_type)
                    )
                except Exception as e:
                    print(f"error processing base64 image: {e}")
                    continue

            # check if it's a plain base64 string (assume PNG if no header)
            elif self._is_base64(image):
                try:
                    image_data = base64.b64decode(image)
                    prepared_images.append(
                        BinaryContent(data=image_data, media_type="image/png")
                    )
                except Exception as e:
                    print(f"error processing base64 image: {e}")
                    continue

            # check if it's a url (starts with http)
            elif image.startswith(("http://", "https://")):
                prepared_images.append(ImageUrl(url=image))

            else:
                # assume it's a local file path, fetch and convert to binarycontent
                try:
                    response = httpx.get(image) if image.startswith("http") else None
                    if response:
                        # for remote images fetched via httpx
                        prepared_images.append(
                            BinaryContent(
                                data=response.content,
                                media_type=response.headers.get(
                                    "content-type", "image/png"
                                ),
                            )
                        )
                    else:
                        # for local file paths
                        with open(image, "rb") as f:
                            file_data = f.read()
                        # determine media type based on file extension
                        media_type = "image/png"
                        if image.lower().endswith(".jpg") or image.lower().endswith(
                            ".jpeg"
                        ):
                            media_type = "image/jpeg"
                        elif image.lower().endswith(".gif"):
                            media_type = "image/gif"

                        prepared_images.append(
                            BinaryContent(data=file_data, media_type=media_type)
                        )
                except Exception as e:
                    print(f"error processing image {image}: {e}")
                    continue

        return prepared_images

    def prepare_documents(self, document_urls: List[str]):
        return [DocumentUrl(url=url) for url in document_urls]

    async def invoke(
        self,
        query: str = "",
        context: Optional[str] = None,
        chat_history: Optional[str] = None,
        images: Optional[List[str]] = None,
        document_urls: Optional[List[str]] = None,
        is_image_output: bool = False,
    ) -> Union[str, BaseModel, BinaryImage]:
        """
        runs the agent with specified query and images

        Args:
            query (str): The query to run the agent with
            context (Optional[str]): Additional context to provide to the agent
            chat_history (Optional[str]): Previous chat history to provide context
            images (Optional[List[str]]): A list of image URLs or local file paths
            document_urls (Optional[List[str]]): A list of document URLs to provide context
        """
        message_content = []
        if query:
            message_content.append(query)
        if context:
            message_content.append(context)
        if chat_history:
            message_content.append(self.format_chat_history(chat_history))
        # add images if provided
        if images:
            images = [images] if isinstance(images, str) else images
            prepped_images = self.prepare_images(images)
            message_content.extend(prepped_images)
        # add documents if provided
        if document_urls:
            prepped_docs = self.prepare_documents(document_urls)
            message_content.extend(prepped_docs)

        try:
            response = await self.agent.run(user_prompt=message_content)
            if hasattr(response, "output") and response.output:
                if is_image_output and hasattr(response.output, "data_uri"):
                    return response.output.data_uri
                return response.output
            return response

        except Exception as e:
            self.logger.error(f"{e}")
            return ""

    @abstractmethod
    async def execute(self, state):
        raise NotImplementedError("")
