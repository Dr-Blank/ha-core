"""Event platform for Fujitsu IR integration."""

import logging
from typing import override

from infrared_protocols.codes.fujitsu.ac import FujitsuACCode
from infrared_protocols.commands.fujitsu_ac import FujitsuAcFixedCommand

from homeassistant.components.event import EventDeviceClass, EventEntity
from homeassistant.components.infrared import (
    InfraredReceivedSignal,
    InfraredReceiverConsumerEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CONF_INFRARED_RECEIVER_ENTITY_ID
from .entity import FujitsuIrEntity

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0

# Power off is deliberately absent: it changes the climate entity's state, which is
# where it is already reported.
_BUTTON_TO_EVENT_TYPE: dict[FujitsuACCode, str] = {
    FujitsuACCode.ECONOMY: "economy",
    FujitsuACCode.POWERFUL: "powerful",
    FujitsuACCode.STEP_VERTICAL_LOUVRE: "step_vertical_louvre",
    FujitsuACCode.STEP_HORIZONTAL_LOUVRE: "step_horizontal_louvre",
    FujitsuACCode.TEST_RUN: "test_run",
    FujitsuACCode.WLAN_ENABLE: "wlan_enable",
    FujitsuACCode.WLAN_DISABLE: "wlan_disable",
    FujitsuACCode.WLAN_CONNECT_METHOD_1: "wlan_connect_method_1",
    FujitsuACCode.WLAN_CONNECT_METHOD_2: "wlan_connect_method_2",
}
_EVENT_TYPE_UNKNOWN = "unknown"
_EVENT_TYPES: list[str] = [*_BUTTON_TO_EVENT_TYPE.values(), _EVENT_TYPE_UNKNOWN]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Fujitsu AC event entity from config entry."""
    if not (receiver_entity_id := entry.data.get(CONF_INFRARED_RECEIVER_ENTITY_ID)):
        return
    async_add_entities([FujitsuIrReceivedCommandEvent(entry, receiver_entity_id)])


class FujitsuIrReceivedCommandEvent(
    FujitsuIrEntity, InfraredReceiverConsumerEntity, EventEntity
):
    """Event entity that fires when a Fujitsu AC remote button is received.

    These buttons carry no state, so the air conditioner keeps the result and nothing
    can be read back. Firing an event is all that can honestly be reported, and it is
    enough to see them in the history and to trigger automations from them.
    """

    _attr_translation_key = "received_command"
    _attr_device_class = EventDeviceClass.BUTTON
    _attr_event_types = _EVENT_TYPES

    def __init__(self, entry: ConfigEntry, receiver_entity_id: str) -> None:
        """Initialize the event entity."""
        super().__init__(entry)
        self._infrared_receiver_entity_id = receiver_entity_id

    @callback
    @override
    def _handle_signal(self, signal: InfraredReceivedSignal) -> None:
        """Handle a received IR signal."""
        command = FujitsuAcFixedCommand.from_raw_timings(signal.timings)
        if command is None or command.code == FujitsuACCode.POWER_OFF:
            return

        try:
            button = FujitsuACCode(command.code)
        except ValueError:
            # A remote has more buttons than are named, and a new one must show up
            # rather than disappear.
            event_type = _EVENT_TYPE_UNKNOWN
        else:
            event_type = _BUTTON_TO_EVENT_TYPE.get(button, _EVENT_TYPE_UNKNOWN)

        _LOGGER.debug(
            "Received Fujitsu AC command: %s (0x%02X)", event_type, command.code
        )

        self._trigger_event(event_type)
        self.async_write_ha_state()
