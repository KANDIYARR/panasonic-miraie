# Changelog

## 1.1.2

- Declare India as the supported region for HACS catalog eligibility.
- Include the refreshed README and supplied MirAIe artwork in the release.
- No device-control changes.

## 1.1.1

Maintained by Vinoth Sakthivel (vinoth@kandiyar.com).

- Prevent OAuth tokens from appearing in debug logs.
- Bound REST and OAuth requests to 30 seconds.
- Separate temporary cloud outages from credential rejection.
- Renew tokens independently of frequent MQTT messages.
- Retain MQTT subscriptions during delayed connections and reconnects.
- Clean up background connections on setup failure and successful unload.
- Report rejected commands without changing the displayed device state.
- Avoid mutating switch channel state before command acceptance.
- Turn fans on when setting a nonzero speed.
- Add privacy-preserving diagnostics, regression tests, and CI checks.
- Set the tested minimum Home Assistant version to 2024.11.3.

Live appliance and newer Home Assistant version testing remain necessary.
