"""N8NConversationAgent: An AbstractConversationAgent that calls an n8n webhook."""
import logging
import uuid
from typing import Any, Literal

from homeassistant.components import conversation
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.httpx_client import get_async_client
from homeassistant.exceptions import HomeAssistantError
from homeassistant.const import MATCH_ALL
from homeassistant.helpers import intent

from .const import DOMAIN, CONF_WEBHOOK_URL, DEFAULT_WEBHOOK_URL

_LOGGER = logging.getLogger(__name__)
DEFAULT_REQUEST_TIMEOUT = 30  # seconds

class N8NConversationAgent(conversation.AbstractConversationAgent):
    """Conversation agent that posts user input to an n8n webhook and maintains conversation history."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the agent."""
        self.hass = hass
        self.entry = entry
        self.webhook_url = entry.data.get(CONF_WEBHOOK_URL, DEFAULT_WEBHOOK_URL)
        # Use an internal dictionary to store conversation histories.
        # Keys are conversation IDs; values are lists of message dicts.
        self.history: dict[str, list[dict]] = {}

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return a list of supported languages."""
        return MATCH_ALL

    async def async_process(
        self, user_input: conversation.ConversationInput
    ) -> conversation.ConversationResult:
        """Process a sentence by sending it along with conversation history to the n8n webhook."""
        # Retrieve existing conversation history if available.
        conversation_id = user_input.conversation_id
        if conversation_id and conversation_id in self.history:
            messages = self.history[conversation_id]
        else:
            # Generate a new conversation_id if not provided.
            try:
                from homeassistant.util import ulid
                conversation_id = ulid.ulid()
            except ImportError:
                conversation_id = str(uuid.uuid4())
            user_input.conversation_id = conversation_id
            messages = []
        
        # Append the user message to the conversation history.
        messages.append({"role": "user", "content": user_input.text})
        self.history[conversation_id] = messages

        # Build payload. Optionally, you can send the whole history if your n8n workflow supports it.
        payload = {
            "user_input": user_input.text,
            "conversation_id": conversation_id,
        }
        _LOGGER.debug("Sending payload - input: %s, conversation_id: %s", user_input.text, conversation_id)

        client = get_async_client(self.hass)
        try:
            response = await client.post(
                self.webhook_url,
                json=payload,
                timeout=DEFAULT_REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
        except Exception as err:
            _LOGGER.error("Error calling n8n webhook: %s", err)
            raise HomeAssistantError("Error calling n8n webhook") from err

        output = data.get("output")
        if output is None:
            _LOGGER.warning("Webhook response missing 'output' key; using empty string")
            output = ""

        _LOGGER.debug("Received JSON response: %s", data)
        _LOGGER.debug("Extracted intent response: %s", output)

        # Prepare intent response.
        intent_response = intent.IntentResponse(language=user_input.language)
        intent_response.async_set_speech(output)

        # Optionally, append the assistant's response to history.
        messages.append({"role": "assistant", "content": output})
        self.history[conversation_id] = messages

        return conversation.ConversationResult(
            response=intent_response,
            conversation_id=conversation_id
        )
