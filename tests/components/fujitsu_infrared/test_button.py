"""Tests for the Fujitsu Infrared button platform."""

from infrared_protocols.codes.fujitsu.ac import FujitsuACCode
import pytest
from syrupy.assertion import SnapshotAssertion

from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN, SERVICE_PRESS
from homeassistant.const import ATTR_ENTITY_ID, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from tests.common import MockConfigEntry, snapshot_platform
from tests.components.common import assert_availability_follows_source_entity
from tests.components.infrared import EMITTER_ENTITY_ID
from tests.components.infrared.common import MockInfraredEmitterEntity

_VERTICAL_ENTITY_ID = "button.fujitsu_ac_move_vertical_louvre"


@pytest.fixture
def platforms() -> list[Platform]:
    """Return platforms to set up."""
    return [Platform.BUTTON]


@pytest.fixture
def has_receiver() -> bool:
    """Return whether the config entry has an infrared receiver configured."""
    return False


@pytest.mark.usefixtures("init_integration")
async def test_entities(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test entity state and registry snapshot."""
    await snapshot_platform(hass, entity_registry, snapshot, mock_config_entry.entry_id)


@pytest.mark.usefixtures("init_integration")
async def test_availability_follows_emitter(hass: HomeAssistant) -> None:
    """Test button availability follows the infrared emitter."""
    await assert_availability_follows_source_entity(
        hass, _VERTICAL_ENTITY_ID, EMITTER_ENTITY_ID
    )


@pytest.mark.parametrize(
    ("entity_id", "button"),
    [
        pytest.param(
            _VERTICAL_ENTITY_ID,
            FujitsuACCode.STEP_VERTICAL_LOUVRE,
            id="step_vertical_louvre",
        ),
        pytest.param(
            "button.fujitsu_ac_move_horizontal_louvre",
            FujitsuACCode.STEP_HORIZONTAL_LOUVRE,
            id="step_horizontal_louvre",
        ),
        pytest.param(
            "button.fujitsu_ac_economy_mode", FujitsuACCode.ECONOMY, id="economy"
        ),
        pytest.param(
            "button.fujitsu_ac_powerful_mode", FujitsuACCode.POWERFUL, id="powerful"
        ),
    ],
)
@pytest.mark.usefixtures("init_integration")
async def test_press_sends_the_action(
    hass: HomeAssistant,
    mock_infrared_emitter_entity: MockInfraredEmitterEntity,
    entity_id: str,
    button: FujitsuACCode,
) -> None:
    """Test each button sends its own util message."""
    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    assert len(mock_infrared_emitter_entity.send_command_calls) == 1
    assert (
        mock_infrared_emitter_entity.send_command_calls[0].get_raw_timings()
        == button.to_command().get_raw_timings()
    )
