from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfRatio, UnitOfTemperature

from atmeexpy.device import Device
from atmeexpy.models import DeviceConditionModel

from .coordinator import AtmeexDataCoordinator
from .entity import AtmeexBaseEntity
from .const import DOMAIN


@dataclass(frozen=True, kw_only=True)
class AtmeexSensorEntityDescription(SensorEntityDescription):
    value_fn: Callable[[DeviceConditionModel], float | int]


SENSORS = (
    AtmeexSensorEntityDescription(
        key="temp_room",
        translation_key="temp_room",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda condition: condition.temp_room / 10,
    ),
    AtmeexSensorEntityDescription(
        key="temp_in",
        translation_key="temp_in",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda condition: condition.temp_in / 10,
    ),
    AtmeexSensorEntityDescription(
        key="hum_room",
        translation_key="hum_room",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda condition: condition.hum_room,
    ),
    AtmeexSensorEntityDescription(
        key="co2_ppm",
        translation_key="co2_ppm",
        device_class=SensorDeviceClass.CO2,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfRatio.PARTS_PER_MILLION,
        value_fn=lambda condition: condition.co2_ppm,
    ),
)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    coordinator: AtmeexDataCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    async_add_entities(
        AtmeexSensorEntity(device, coordinator, description)
        for device in coordinator.devices.values()
        for description in SENSORS
    )


class AtmeexSensorEntity(AtmeexBaseEntity, SensorEntity):

    entity_description: AtmeexSensorEntityDescription

    def __init__(self, device: Device, coordinator: AtmeexDataCoordinator, description: AtmeexSensorEntityDescription):
        # Base __init__ calls _update_state, which needs the description
        self.entity_description = description
        super().__init__(device, coordinator)

        self._attr_unique_id = f"{device.model.id}_{description.key}"

    def _update_state(self):
        condition = self.device.model.condition
        self._attr_native_value = self.entity_description.value_fn(condition) if condition else None
