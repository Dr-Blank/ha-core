"""Common entity for Fujitsu IR integration."""

from infrared_protocols.commands.fujitsu_ac import FujitsuAcProtocol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PROTOCOL
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, PROTOCOL_EXTENDED


class FujitsuIrEntity(Entity):
    """Fujitsu IR base entity providing common device info."""

    _attr_has_entity_name = True

    def __init__(
        self,
        entry: ConfigEntry,
        unique_id_suffix: str | None = None,
        device_name: str = "Fujitsu AC",
    ) -> None:
        """Initialize Fujitsu IR entity."""
        # Unique IDs are already unique per platform, so a platform that holds a single
        # entity needs no suffix at all.
        self._attr_unique_id = (
            entry.entry_id
            if unique_id_suffix is None
            else f"{entry.entry_id}_{unique_id_suffix}"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=device_name,
            manufacturer="Fujitsu General",
        )


def config_entry_protocol(entry: ConfigEntry) -> FujitsuAcProtocol:
    """Return the protocol the configured remote family speaks."""
    if entry.data.get(CONF_PROTOCOL) == PROTOCOL_EXTENDED:
        return FujitsuAcProtocol.EXTENDED
    return FujitsuAcProtocol.STANDARD
