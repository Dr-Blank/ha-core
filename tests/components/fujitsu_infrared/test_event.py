"""Tests for the Fujitsu Infrared event platform."""

from infrared_protocols.codes.fujitsu.ac import FujitsuACCode
from infrared_protocols.commands.fujitsu_ac import (
    FujitsuAcCommand,
    FujitsuAcFixedCommand,
)
import pytest
from syrupy.assertion import SnapshotAssertion

from homeassistant.components.event import ATTR_EVENT_TYPE
from homeassistant.components.infrared import InfraredReceivedSignal
from homeassistant.const import STATE_UNKNOWN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from tests.common import MockConfigEntry, snapshot_platform
from tests.components.infrared.common import MockInfraredReceiverEntity

_EVENT_ENTITY_ID = "event.fujitsu_ac_remote_button"


@pytest.fixture
def platforms() -> list[Platform]:
    """Return platforms to set up."""
    return [Platform.EVENT]


@pytest.mark.usefixtures("init_integration")
async def test_entities(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test entity state and registry snapshot."""
    await snapshot_platform(hass, entity_registry, snapshot, mock_config_entry.entry_id)


@pytest.mark.parametrize("has_receiver", [False])
@pytest.mark.usefixtures("init_integration")
async def test_no_event_entity_without_a_receiver(hass: HomeAssistant) -> None:
    """Test nothing can be received without a receiver, so no entity is created."""
    assert hass.states.get(_EVENT_ENTITY_ID) is None


@pytest.mark.parametrize(
    ("button", "expected"),
    [
        pytest.param(FujitsuACCode.ECONOMY, "economy", id="economy"),
        pytest.param(FujitsuACCode.POWERFUL, "powerful", id="powerful"),
        pytest.param(
            FujitsuACCode.STEP_VERTICAL_LOUVRE,
            "step_vertical_louvre",
            id="step_vertical_louvre",
        ),
        pytest.param(
            FujitsuACCode.STEP_HORIZONTAL_LOUVRE,
            "step_horizontal_louvre",
            id="step_horizontal_louvre",
        ),
        pytest.param(FujitsuACCode.TEST_RUN, "test_run", id="test_run"),
        pytest.param(FujitsuACCode.WLAN_ENABLE, "wlan_enable", id="wlan_enable"),
        pytest.param(FujitsuACCode.WLAN_DISABLE, "wlan_disable", id="wlan_disable"),
        pytest.param(
            FujitsuACCode.WLAN_CONNECT_METHOD_1,
            "wlan_connect_method_1",
            id="wlan_connect_method_1",
        ),
        pytest.param(
            FujitsuACCode.WLAN_CONNECT_METHOD_2,
            "wlan_connect_method_2",
            id="wlan_connect_method_2",
        ),
    ],
)
@pytest.mark.usefixtures("init_integration")
async def test_remote_button_fires_an_event(
    hass: HomeAssistant,
    mock_infrared_receiver_entity: MockInfraredReceiverEntity,
    button: FujitsuACCode,
    expected: str,
) -> None:
    """Test every fixed code a remote sends shows up as its own event type."""
    mock_infrared_receiver_entity._handle_received_signal(
        InfraredReceivedSignal(timings=button.to_command().get_raw_timings())
    )
    await hass.async_block_till_done()

    state = hass.states.get(_EVENT_ENTITY_ID)
    assert state is not None
    assert state.attributes[ATTR_EVENT_TYPE] == expected


@pytest.mark.usefixtures("init_integration")
async def test_unnamed_code_fires_an_unknown_event(
    hass: HomeAssistant, mock_infrared_receiver_entity: MockInfraredReceiverEntity
) -> None:
    """Test a button this integration does not name still shows up."""
    mock_infrared_receiver_entity._handle_received_signal(
        InfraredReceivedSignal(
            timings=FujitsuAcFixedCommand(code=0x7F).get_raw_timings()
        )
    )
    await hass.async_block_till_done()

    state = hass.states.get(_EVENT_ENTITY_ID)
    assert state is not None
    assert state.attributes[ATTR_EVENT_TYPE] == "unknown"


@pytest.mark.parametrize(
    "timings",
    [
        pytest.param(
            FujitsuACCode.POWER_OFF.to_command().get_raw_timings(), id="power_off"
        ),
        pytest.param(
            FujitsuAcCommand(temperature=24).get_raw_timings(), id="state_message"
        ),
        pytest.param([100, -100, 200, -200], id="not_fujitsu"),
    ],
)
@pytest.mark.usefixtures("init_integration")
async def test_signals_that_fire_no_event(
    hass: HomeAssistant,
    mock_infrared_receiver_entity: MockInfraredReceiverEntity,
    timings: list[int],
) -> None:
    """Test only the stateless buttons fire here.

    Power off and the state message both change the climate entity, which is where
    they are already reported, so repeating them as events would be noise.
    """
    mock_infrared_receiver_entity._handle_received_signal(
        InfraredReceivedSignal(timings=timings)
    )
    await hass.async_block_till_done()

    state = hass.states.get(_EVENT_ENTITY_ID)
    assert state is not None
    assert state.state == STATE_UNKNOWN
