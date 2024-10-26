"""Button for Shelly."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.ialarm_controller.entity import IAlarmEntity

from . import IAlarmConfigEntry
from .coordinator import IAlarmCoordinator


@dataclass(frozen=True, kw_only=True)
class IAlarmButtonDescription(ButtonEntityDescription):
    """Describe an iAlarm button entity.

    Attributes:
        press_action: A callable that takes an IAlarmCoordinator
        instance and returns a coroutine to be awaited.

    """

    press_action: Callable[[IAlarmCoordinator], Awaitable[None]]


BUTTONS: tuple[IAlarmButtonDescription, ...] = (
    IAlarmButtonDescription(
        key="CANCEL",
        name="Cancel alarm alerts",
        icon="mdi:playlist-remove",
        translation_key="cancel",
        entity_category=EntityCategory.CONFIG,
        press_action=lambda coordinator: coordinator.async_cancel_alarm(),
    ),
    IAlarmButtonDescription(
        key="LOGS",
        name="Log alerts",
        icon="mdi:math-log",
        translation_key="logs",
        entity_category=EntityCategory.DIAGNOSTIC,
        press_action=lambda coordinator: coordinator.async_get_log(),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: IAlarmConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up iAlarm button entities from a config entry.

    This function is called when the iAlarm config entry is set up in Home Assistant.
    It creates and registers button entities based on the configuration.

    Args:
        hass: Home Assistant instance.
        config_entry: The configuration entry for the iAlarm integration.
        async_add_entities: Callback to add entities to Home Assistant.

    Returns:
        None

    """
    coordinator = config_entry.runtime_data
    unique_id = config_entry.unique_id
    assert unique_id is not None

    async_add_entities(
        (
            IAlarmButton(coordinator, unique_id, config_entry.title, description)
            for description in BUTTONS
        ),
        True,
    )


class IAlarmButton(IAlarmEntity, ButtonEntity):
    """Represent a button entity for the iAlarm system.

    This class is responsible for defining the behavior of buttons
    that can trigger actions in the iAlarm system. It extends the
    functionality of the ButtonEntity from Home Assistant to
    facilitate custom actions based on the iAlarm integration.

    Attributes:
        entity_description (IAlarmButtonDescription):
            The description of the button entity, containing metadata
            such as action and key for the button.

    """

    entity_description: IAlarmButtonDescription

    def __init__(
        self,
        coordinator: IAlarmCoordinator,
        unique_id: str,
        name: str,
        description: IAlarmButtonDescription,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, unique_id, name)
        self._attr_unique_id = f"{unique_id}_{description.key}"
        self.entity_description = description

    async def async_press(self) -> None:
        """Trigger the button action."""
        await self.entity_description.press_action(self.coordinator)
