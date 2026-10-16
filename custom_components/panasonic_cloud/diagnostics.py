# Modified by Vinoth Sakthivel, 2026. See NOTICE for attribution.
"""Privacy-preserving diagnostics for Panasonic MirAIe."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict:
    """Report transport health without tokens, identifiers or household data."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    return {
        "device_counts": {
            category: len(devices)
            for category, devices in coordinator.devices.items()
        },
        "mqtt_connected": bool(coordinator.mqtt and coordinator.mqtt.is_connected),
        "mqtt_topic_count": len(coordinator.topics),
        "last_update_success": coordinator.last_update_success,
        "cached_device_count": len(coordinator.device_status),
    }
