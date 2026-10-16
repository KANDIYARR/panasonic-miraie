# Modified by Vinoth Sakthivel, 2026. See NOTICE for attribution.
"""The Panasonic MirAIe integration."""
from __future__ import annotations

import logging
import asyncio

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import (
    aiohttp_client,
    config_validation as cv,
    config_entry_oauth2_flow,
)

from .api import PanasonicMirAIeAPI
from .config_flow import PanasonicMirAIeOAuth2Implementation
from .const import DOMAIN
from .coordinator import PanasonicMirAIeCoordinator

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CLIMATE, Platform.FAN, Platform.SWITCH]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Panasonic MirAIe component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Panasonic MirAIe from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    config_entry_oauth2_flow.async_register_implementation(
        hass,
        DOMAIN,
        PanasonicMirAIeOAuth2Implementation(hass),
    )

    try:
        implementation = (
            await config_entry_oauth2_flow.async_get_config_entry_implementation(
                hass, entry
            )
        )
    except ValueError as err:
        _LOGGER.error("OAuth2 implementation not found: %s", err)
        raise ConfigEntryNotReady(
            "OAuth2 implementation not available"
        ) from err

    oauth_session = config_entry_oauth2_flow.OAuth2Session(
        hass, entry, implementation
    )

    try:
        await oauth_session.async_ensure_token_valid()
    except aiohttp.ClientResponseError as err:
        if err.status in (400, 401, 403):
            raise ConfigEntryAuthFailed("Please re-authenticate") from err
        raise ConfigEntryNotReady("Token service unavailable") from err
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as err:
        raise ConfigEntryNotReady("Unable to validate token") from err

    token_data = entry.data.get("token", {})
    access_token = token_data.get("access_token", "")

    if not access_token:
        raise ConfigEntryAuthFailed("No access token available")

    session = aiohttp_client.async_get_clientsession(hass)
    api = PanasonicMirAIeAPI(session, access_token)

    coordinator = PanasonicMirAIeCoordinator(
        hass, api, entry, oauth_session
    )

    try:
        await coordinator.async_discover_devices()
        await coordinator.async_config_entry_first_refresh()
        hass.data[DOMAIN][entry.entry_id] = {
            "coordinator": coordinator,
            "api": api,
            "oauth_session": oauth_session,
        }
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except BaseException as err:
        await coordinator.async_shutdown_mqtt()
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if isinstance(err, (ConfigEntryAuthFailed, asyncio.CancelledError)):
            raise
        raise ConfigEntryNotReady("Unable to set up Panasonic MirAIe") from err
    coordinator.async_start_token_maintenance()

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry - ensures MQTT is disconnected cleanly."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id, None)
        if data is not None:
            await data["coordinator"].async_shutdown_mqtt()
    return unload_ok
