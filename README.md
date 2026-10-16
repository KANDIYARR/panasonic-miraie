# Panasonic MirAIe

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://www.hacs.xyz/docs/faq/custom_repositories/)
[![Tests](https://github.com/KANDIYARR/panasonic-miraie/actions/workflows/tests.yml/badge.svg)](https://github.com/KANDIYARR/panasonic-miraie/actions/workflows/tests.yml)
[![HACS validation](https://github.com/KANDIYARR/panasonic-miraie/actions/workflows/hacs.yml/badge.svg)](https://github.com/KANDIYARR/panasonic-miraie/actions/workflows/hacs.yml)

Control Panasonic MirAIe air conditioners, fans, switches and plugs from Home
Assistant, with MQTT state updates and REST fallback.

**Author and maintainer:** [Vinoth Sakthivel](https://github.com/KANDIYARR) ·
[vinoth@kandiyar.com](mailto:vinoth@kandiyar.com)

An independent maintenance fork of
[miraiehomeassistant/ha-panasonic-miraie](https://github.com/miraiehomeassistant/ha-panasonic-miraie).
Original attribution and the Apache 2.0 license are preserved.

## Requirements

- Home Assistant **2024.11.3 or newer**. Automated tests use 2024.11.3; later
  releases and live appliances need deployment testing.
- HACS for the recommended installation method.
- A MirAIe account with devices already paired in the mobile app.
- Internet access to Panasonic's HTTPS services and `mqtt.miraie.in:8883`.

## Install with HACS

[![Open your Home Assistant instance and add this repository to HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=KANDIYARR&repository=panasonic-miraie&category=integration)

1. Open **HACS → ⋮ → Custom repositories**.
2. Add `https://github.com/KANDIYARR/panasonic-miraie` with type **Integration**.
3. Find **Panasonic MirAIe** and download the latest release.
4. Restart Home Assistant.
5. Open **Settings → Devices & services → Add integration → Panasonic MirAIe**.
6. Follow the Panasonic OAuth login and link your account.

This repository is distributed as a HACS **custom repository**. It is not a
claim of inclusion in the HACS default catalog.

### Upgrading from upstream

Back up your Home Assistant configuration first. Remove the original repository
from HACS before adding this fork so only one repository manages the integration.
Install this fork over the existing `custom_components/panasonic_cloud` folder
and restart. Keep the existing Home Assistant integration entry: the domain and
entity unique IDs are unchanged, so existing entities and automations can be reused.
Do not install both versions under different component folders.

### Manual installation

Download `panasonic-miraie-1.1.1.zip` from
[Releases](https://github.com/KANDIYARR/panasonic-miraie/releases).
Copy its `custom_components/panasonic_cloud` folder into your Home Assistant
`config/custom_components/` directory and restart. Then follow steps 5–6 above.

## Supported devices

| Device | Features |
| --- | --- |
| Air conditioner (`AC`, `ODMIRB-AC`) | Power, HVAC mode, target temperature, fan speed |
| Fan (`FANCONTROLLER`) | Power, five speed levels, auto/normal/turbo/sleep presets |
| Switches and plugs (`SWITCHES`, `ROMASWITCHES`, `PLUG`) | Power and multichannel switch control |

## Improvements in 1.1.1

- No OAuth response bodies in logs; REST and OAuth requests have 30-second limits.
- Temporary cloud failures retry without incorrectly demanding another login.
- Independent token checks prevent frequent MQTT updates delaying renewal.
- MQTT remembers subscriptions across delayed connections and reconnects.
- Failed commands report errors without falsely changing the displayed state.
- Setup failures and successful unloads clean up connections and renewal timers.
- Nonzero fan speed commands power on the fan; switch commands preserve cached
  channel state until transport acceptance.
- Downloadable diagnostics report counts and transport health without tokens,
  account identifiers, device identifiers, or device names.

See [CHANGELOG.md](CHANGELOG.md) and [REVIEW.md](REVIEW.md) for details.

## Troubleshooting

- **No devices:** confirm the account and paired devices in the MirAIe app.
  Reload the integration after adding devices in the app.
- **Unavailable:** check the device in the app and cloud/network connectivity.
- **Reauthentication:** use Home Assistant's reauthentication prompt to log in
  again without removing the integration.
- **No instant updates:** allow outbound MQTT port 8883. REST polling remains
  available as a fallback, normally after 15 minutes without push updates.
- **Report a problem:** open an [issue](https://github.com/KANDIYARR/panasonic-miraie/issues)
  with your HA version, device category, and integration diagnostics. Do not post
  access tokens, refresh tokens, or credentials.

## Limitations

Cloud connectivity is required. MQTT transport acceptance is not confirmation
that an appliance applied a command. MQTT authentication uses the first home ID;
access across multiple homes remains unverified. Unsupported REST status queries
rely on MQTT. Energy monitoring and additional appliance categories are not
implemented. Live OAuth, hardware behavior, and newer HA versions still need testing.

## Development

Use Python 3.12:

```sh
pip install -r requirements-test.txt
ruff check custom_components tests
pytest -q
```

Tests use real Home Assistant classes with mocked cloud transports. GitHub
Actions runs regression tests, HACS validation and Hassfest checks.

## License and credits

[Apache License 2.0](LICENSE). See [AUTHORS.md](AUTHORS.md).
Upstream attribution: Panasonic Innovation Centre India and contributors.
This fork is independently maintained by Vinoth Sakthivel and is not an official
Panasonic release.
