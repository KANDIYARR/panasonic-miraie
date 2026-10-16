"""Offline regressions using real Home Assistant classes and mocked transports."""
import asyncio
from unittest.mock import AsyncMock, Mock

import aiohttp
import pytest
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.panasonic_cloud.api import PanasonicMirAIeAPI
from custom_components.panasonic_cloud.coordinator import PanasonicMirAIeCoordinator
from custom_components.panasonic_cloud.mqtt_handler import PanasonicMirAIeMQTT


def coordinator():
    obj = object.__new__(PanasonicMirAIeCoordinator)
    obj.api = Mock(access_token="token")
    obj.api.async_set_device_state = AsyncMock(return_value=True)
    obj.api.async_get_device_status = AsyncMock()
    obj.oauth_session = Mock(async_ensure_token_valid=AsyncMock())
    obj.entry = Mock(data={"token": {"access_token": "token"}})
    obj.device_status = {"ac": {"acdc": "off"}}
    obj.devices = {"ac": [{"deviceId": "ac"}]}
    obj.mqtt = None
    obj.async_set_updated_data = Mock()
    return obj


@pytest.mark.asyncio
async def test_rejected_control_preserves_state():
    obj = coordinator()
    obj.api.async_set_device_state.return_value = False
    with pytest.raises(HomeAssistantError):
        await obj.async_send_control("ac", None, {"acdc": "on"})
    assert obj.device_status["ac"]["acdc"] == "off"
    obj.async_set_updated_data.assert_not_called()


@pytest.mark.asyncio
async def test_mqtt_failure_uses_rest():
    obj = coordinator()
    obj.mqtt = Mock(is_connected=True, publish_control=Mock(return_value=False))
    assert await obj.async_send_control("ac", "prefix/home/ac", {"acdc": "on"})
    obj.api.async_set_device_state.assert_awaited_once()
    assert obj.device_status["ac"]["acdc"] == "on"


@pytest.mark.asyncio
@pytest.mark.parametrize("status,expected", [(401, ConfigEntryAuthFailed), (503, UpdateFailed)])
async def test_token_error_classification(status, expected):
    obj = coordinator()
    obj.oauth_session.async_ensure_token_valid.side_effect = aiohttp.ClientResponseError(
        request_info=Mock(), history=(), status=status
    )
    with pytest.raises(expected):
        await obj._async_ensure_fresh_token()


@pytest.mark.asyncio
async def test_poll_outage_is_not_success():
    obj = coordinator()
    obj.api.async_get_device_status.side_effect = aiohttp.ClientConnectionError()
    with pytest.raises(UpdateFailed):
        await obj._async_update_data()
    assert obj.device_status["ac"]["onlineStatus"] == "false"


@pytest.mark.asyncio
async def test_deferred_subscriptions_survive_connect():
    obj = PanasonicMirAIeMQTT(asyncio.get_running_loop(), "home", "token", Mock())
    obj.subscribe_topics(["prefix/home/ac"])
    client = Mock()
    obj._on_connect(client, None, None, 0)
    assert {call.args[0] for call in client.subscribe.call_args_list} == {
        "prefix/home/ac/status", "prefix/home/ac/connectionStatus"
    }


@pytest.mark.asyncio
async def test_malformed_mqtt_payload_ignored():
    callback = Mock()
    obj = PanasonicMirAIeMQTT(asyncio.get_running_loop(), "home", "token", callback)
    for payload in [b'[]', b'null', b'broken']:
        await obj._handle_message("prefix/home/ac/status", payload)
    callback.assert_not_called()
    await obj._handle_message("prefix/home/ac/status", b'{"acdc":"on"}')
    callback.assert_called_once_with("ac", {"acdc": "on"})


@pytest.mark.asyncio
async def test_home_server_error_propagates():
    response = Mock(status=502)
    response.raise_for_status.side_effect = aiohttp.ClientResponseError(
        request_info=Mock(), history=(), status=502
    )
    context = AsyncMock()
    context.__aenter__.return_value = response
    session = Mock(get=Mock(return_value=context))
    with pytest.raises(aiohttp.ClientResponseError):
        await PanasonicMirAIeAPI(session, "token").async_get_homes()


@pytest.mark.asyncio
async def test_token_response_not_logged(caplog, monkeypatch):
    import logging
    from custom_components.panasonic_cloud import config_flow

    response = Mock(status=200)
    response.text = AsyncMock(return_value='{"access_token":"VERY_SECRET","expires_in":7776000}')
    context = AsyncMock()
    context.__aenter__.return_value = response
    monkeypatch.setattr(config_flow, "async_get_clientsession", lambda hass: Mock(post=Mock(return_value=context)))
    implementation = config_flow.PanasonicMirAIeOAuth2Implementation(Mock())
    with caplog.at_level(logging.DEBUG):
        result = await implementation._token_request({"grant_type": "authorization_code"})
    assert result["expires_in"] == 3600
    assert "VERY_SECRET" not in caplog.text
    context.__aexit__.assert_awaited_once()


@pytest.mark.asyncio
async def test_switch_failure_does_not_mutate_channel_cache():
    from custom_components.panasonic_cloud.switch import PanasonicSwitch

    obj = coordinator()
    obj.device_status["ac"] = {"states": [{"rmcn": "00", "rmcps": "off"}]}
    obj.api.async_set_device_state.return_value = False
    entity = PanasonicSwitch(obj, {"deviceId": "ac"}, "00")
    with pytest.raises(HomeAssistantError):
        await entity.async_turn_on()
    assert obj.device_status["ac"]["states"][0]["rmcps"] == "off"


@pytest.mark.asyncio
async def test_fan_speed_powers_on():
    from custom_components.panasonic_cloud.fan import PanasonicFan

    obj = coordinator()
    obj.async_send_control = AsyncMock()
    entity = PanasonicFan(obj, {"deviceId": "ac"})
    await entity.async_set_percentage(60)
    obj.async_send_control.assert_awaited_once_with("ac", None, {"ps": "on", "fafs": 3})


@pytest.mark.asyncio
async def test_failed_unload_keeps_mqtt_alive():
    from custom_components.panasonic_cloud import async_unload_entry

    obj = coordinator()
    obj.async_shutdown_mqtt = AsyncMock()
    hass = Mock(data={"panasonic_cloud": {"entry": {"coordinator": obj}}})
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=False)
    assert not await async_unload_entry(hass, Mock(entry_id="entry"))
    obj.async_shutdown_mqtt.assert_not_awaited()


@pytest.mark.asyncio
async def test_successful_unload_stops_mqtt():
    from custom_components.panasonic_cloud import async_unload_entry

    obj = coordinator()
    obj.async_shutdown_mqtt = AsyncMock()
    hass = Mock(data={"panasonic_cloud": {"entry": {"coordinator": obj}}})
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    assert await async_unload_entry(hass, Mock(entry_id="entry"))
    obj.async_shutdown_mqtt.assert_awaited_once()
    assert not hass.data["panasonic_cloud"]


def test_platform_imports():
    from custom_components.panasonic_cloud import climate, fan, switch

    assert climate.PanasonicClimate
    assert fan.PanasonicFan
    assert switch.PanasonicSwitch


@pytest.mark.asyncio
async def test_setup_failure_closes_mqtt(monkeypatch):
    from custom_components import panasonic_cloud as integration

    obj = coordinator()
    obj.async_discover_devices = AsyncMock()
    obj.async_config_entry_first_refresh = AsyncMock(side_effect=UpdateFailed("offline"))
    obj.async_shutdown_mqtt = AsyncMock()
    monkeypatch.setattr(integration, "PanasonicMirAIeCoordinator", Mock(return_value=obj))
    monkeypatch.setattr(integration, "PanasonicMirAIeOAuth2Implementation", Mock())
    monkeypatch.setattr(integration.aiohttp_client, "async_get_clientsession", Mock())
    monkeypatch.setattr(integration.config_entry_oauth2_flow, "async_register_implementation", Mock())
    monkeypatch.setattr(integration.config_entry_oauth2_flow, "async_get_config_entry_implementation", AsyncMock())
    monkeypatch.setattr(integration.config_entry_oauth2_flow, "OAuth2Session", Mock(return_value=obj.oauth_session))
    from homeassistant.exceptions import ConfigEntryNotReady

    with pytest.raises(ConfigEntryNotReady):
        await integration.async_setup_entry(Mock(data={}), obj.entry)
    obj.async_shutdown_mqtt.assert_awaited_once()


@pytest.mark.asyncio
async def test_poll_recovers_from_outage():
    obj = coordinator()
    obj.device_status["ac"]["onlineStatus"] = "false"
    obj.api.async_get_device_status.return_value = {"acdc": "on"}
    await obj._async_update_data()
    assert obj.device_status["ac"]["onlineStatus"] == "true"


@pytest.mark.asyncio
async def test_diagnostics_excludes_identifiers():
    from custom_components.panasonic_cloud.diagnostics import async_get_config_entry_diagnostics

    obj = coordinator()
    obj.topics = ["private/home/topic"]
    obj.last_update_success = True
    hass = Mock(data={"panasonic_cloud": {"entry": {"coordinator": obj}}})
    result = await async_get_config_entry_diagnostics(hass, Mock(entry_id="entry"))
    assert result["device_counts"] == {"ac": 1}
    assert "private" not in str(result)
    assert "token" not in str(result)
