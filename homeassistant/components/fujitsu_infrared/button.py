"""Button platform for Fujitsu IR integration — stateless remote actions."""

from dataclasses import dataclass
from typing import override

from infrared_protocols.codes.fujitsu.ac import FujitsuACCode

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.components.infrared import InfraredEmitterConsumerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CONF_INFRARED_ENTITY_ID
from .entity import FujitsuIrEntity

PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class FujitsuIrButtonEntityDescription(ButtonEntityDescription):
    """Describes a Fujitsu IR button."""

    command_code: FujitsuACCode


# The unit keeps the state for all of these, and the remote only ever says "again",
# so there is nothing for the integration to report back and they are buttons rather
# than switches or swing options.
BUTTON_DESCRIPTIONS: tuple[FujitsuIrButtonEntityDescription, ...] = (
    FujitsuIrButtonEntityDescription(
        key="step_vertical_louvre",
        translation_key="step_vertical_louvre",
        command_code=FujitsuACCode.STEP_VERTICAL_LOUVRE,
    ),
    FujitsuIrButtonEntityDescription(
        key="step_horizontal_louvre",
        translation_key="step_horizontal_louvre",
        command_code=FujitsuACCode.STEP_HORIZONTAL_LOUVRE,
    ),
    FujitsuIrButtonEntityDescription(
        key="economy",
        translation_key="economy",
        command_code=FujitsuACCode.ECONOMY,
    ),
    FujitsuIrButtonEntityDescription(
        key="powerful",
        translation_key="powerful",
        command_code=FujitsuACCode.POWERFUL,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Fujitsu AC buttons from a config entry."""
    emitter_entity_id = entry.data[CONF_INFRARED_ENTITY_ID]
    async_add_entities(
        FujitsuIrButton(entry, emitter_entity_id, description)
        for description in BUTTON_DESCRIPTIONS
    )


class FujitsuIrButton(FujitsuIrEntity, InfraredEmitterConsumerEntity, ButtonEntity):
    """A single stateless action a Fujitsu General remote can send."""

    entity_description: FujitsuIrButtonEntityDescription

    def __init__(
        self,
        entry: ConfigEntry,
        emitter_entity_id: str,
        description: FujitsuIrButtonEntityDescription,
    ) -> None:
        """Initialize the button."""
        super().__init__(entry, unique_id_suffix=description.key)
        self.entity_description = description
        self._infrared_emitter_entity_id = emitter_entity_id

    @override
    async def async_press(self) -> None:
        """Send the action's message."""
        await self._send_command(self.entity_description.command_code.to_command())
