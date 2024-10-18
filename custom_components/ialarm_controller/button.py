"""Button for Shelly."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass

from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.ialarm_controller.const import SERVICE_GET_LOG_MAX_ENTRIES
from custom_components.ialarm_controller.entity import IAlarmEntity

from . import IAlarmConfigEntry
from .coordinator import IAlarmCoordinator


@dataclass(frozen=True, kw_only=True)
class IAlarmButtonDescription(ButtonEntityDescription):
    press_action: Callable[[IAlarmCoordinator], Coroutine]


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
    coordinator = config_entry.runtime_data
    unique_id = config_entry.unique_id
    assert unique_id is not None

    async_add_entities(
        IAlarmButton(coordinator, unique_id, config_entry.title, description)
        for description in BUTTONS
    )


class IAlarmButton(IAlarmEntity, ButtonEntity):
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
