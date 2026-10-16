# Review and maintenance release 1.1.1

Based on upstream commit `9f32c8e0da7818e0fce11067ac45fa3c32dc8681`.

## Resolved findings

| Finding | Change |
| --- | --- |
| OAuth responses included bearer tokens in debug output | Removed response-body logging and closed responses with context managers |
| Cloud outages were classified as invalid credentials | Separate HTTP credential rejection from connection, timeout and server errors |
| Requests had no integration-specific timeout | Added 30-second bounds to REST and OAuth requests |
| Failed discovery could appear as an empty successful account | Propagate server failures so setup retries |
| Commands updated cached state before knowing whether submission succeeded | Update only after transport acceptance; surface rejected commands |
| Switch channel commands shared mutable cached dictionaries | Copy channel dictionaries before constructing commands |
| Fan speed changes did not power on an off fan | Include power-on in nonzero speed commands |
| MQTT subscription lists were lost when initial connection was delayed | Remember requested subscriptions before connecting and replay on reconnect |
| MQTT synchronous initial connection hindered startup recovery | Start asynchronous connection with background reconnect |
| MQTT client IDs collided across installations of the same home | Generate a unique connection ID |
| MQTT thread stop blocked the event loop | Stop the thread in an executor |
| First-refresh failure left MQTT running | Clean up connections on setup failure |
| Unload disconnected MQTT even if platform unload failed | Disconnect only after successful platform unload |
| Frequent push updates deferred token maintenance | Add independent five-minute credential checks |
| Failed polls reported success with stale state | Track device failure and raise coordinator failure on complete outage |
| Unsupported minimum HA version and unbounded MQTT dependency | Set tested baseline to HA 2024.11.3 and pin Paho 2.1.0 |

## Verification

17 offline regression tests passed on Python 3.12 / Home Assistant 2024.11.3.
Ruff and `git diff --check` passed. Tests use real HA classes and mocked cloud
transports; no appliance controls or user credentials were used. Dependency
warnings from the baseline's HTTP/ACME stack are not integration failures.

## Remaining release checks

- Repository: https://github.com/KANDIYARR/panasonic-miraie
- Maintainer: Vinoth Sakthivel (vinoth@kandiyar.com).
- Run the included hosted HACS and Hassfest workflows in that repository.
- Validate real OAuth login/reauthentication, token rollover, offline recovery,
  and AC/fan/multichannel switch behavior on hardware.
- Test on the deployment's current Home Assistant version. The baseline test
  is not a claim that every later release has been validated.
- MQTT uses the first home ID for authentication, as upstream does. Access to
  devices in other homes remains unverified.
- MQTT publish success is local transport acceptance, not appliance acknowledgement.
- Unsupported REST status queries still rely on MQTT for device state.
- Discovery occurs at entry setup; reload after adding devices in the MirAIe app.

## Upstream references

- https://github.com/miraiehomeassistant/ha-panasonic-miraie
- https://developers.home-assistant.io/docs/integration_fetching_data/
- https://www.hacs.xyz/docs/publish/integration/
