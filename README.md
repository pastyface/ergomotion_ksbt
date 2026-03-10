# Ergomotion KSBT for Home Assistant

[![Open your Home Assistant instance and open this repository inside HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=dewir&repository=ergomotion_ksbt&category=integration)

Custom Home Assistant integration for KSBT-based Ergomotion beds over Bluetooth Low Energy.

This project was built from live protocol testing against a real bed. It targets the Nordic UART based KSBT control path, which is different from the older FFE4/FFE9 Ergomotion protocol used by some other integrations.

## Current status

- HACS-ready repository layout
- Config flow for Bluetooth address setup
- Optimistic control entities for the commands verified on hardware
- Domain services for scripts and automations
- Best-effort decoding for token, light-state, heartbeat, massage, and snapshot notification families
- Verified command prelude and control frames for KSBT beds

## Verified controls

These commands were tested live against the target bed:

- Back Up
- Back Down
- Feet Up
- Feet Down
- Lumbar Up
- Lumbar Down
- Zero G
- Flat
- Relax
- Anti Snore
- TV
- Memory
- Massage All
- Massage Head
- Massage Foot
- Massage Timer
- Light

## What the integration exposes today

- `cover` entities
  - Head
  - Feet
  - Lumbar
- `number` entities
  - Head Hold Duration
  - Feet Hold Duration
  - Lumbar Hold Duration
- `button` entities
  - Back Up
  - Back Down
  - Feet Up
  - Feet Down
  - Lumbar Up
  - Lumbar Down
  - Stop
  - Zero G
  - Flat
  - Relax
  - Anti Snore
  - TV
  - Memory
  - Massage All
  - Massage Head
  - Massage Foot
  - Massage Timer
  - Light
- `select` entities
  - Preset
  - Massage Mode
- `sensor`
  - Last Notification
  - Notification Type
  - Last Token
  - Token Counter
  - Light Level
  - Massage Timer
  - Snapshot Counter
- `binary_sensor`
  - Connection
  - Light Enabled
  - Massage Head Active
  - Massage Foot Active
- domain services
  - `ergomotion_ksbt.prepare`
  - `ergomotion_ksbt.press_action`
  - `ergomotion_ksbt.hold_action`
  - `ergomotion_ksbt.stop`
  - `ergomotion_ksbt.set_debug_logging`
  - `ergomotion_ksbt.dump_debug_state`

## Important limitation

This first version is command-focused, not state-decoding focused.

- The three cover entities are optimistic step controls.
- A cover press sends a timed hold, then an automatic stop.
- Head, feet, and lumbar hold durations are configurable from the integration options page.
- Those same values are also exposed as `number` entities for dashboard tuning.
- Directional motion is also available as dedicated quick-action `button` entities.
- The `select` entities are optimistic command launchers that remember the last chosen option.
- Notification decoding is intentionally conservative and only covers packet families we have actually observed.
- Position telemetry is still not fully decoded yet.

That still makes it useful for daily control and gives us a clean base to extend once the remaining status packets are understood.

## Installation

### HACS

1. Add this repository as a custom repository in HACS with type `Integration`.
2. Install `Ergomotion KSBT`.
3. Restart Home Assistant.
4. Go to `Settings -> Devices & Services -> Add Integration`.
5. Search for `Ergomotion KSBT`.

### Manual

Copy `custom_components/ergomotion_ksbt` into your Home Assistant `custom_components` directory and restart Home Assistant.

## Configuration

The config flow can use Bluetooth discovery or a manually entered MAC address.

After setup, the integration options page lets you tune separate hold durations for head, feet, and lumbar movements.

Those same values are also exposed as `number` entities so you can adjust them from a dashboard.

The current matcher is aimed at devices whose local name starts with `KSBT`.

## Services

Example service calls:

```yaml
service: ergomotion_ksbt.press_action
data:
  action: zero_g
```

```yaml
service: ergomotion_ksbt.hold_action
data:
  action: back_up
  duration: 3.0
```

```yaml
service: ergomotion_ksbt.set_debug_logging
data:
  enabled: true
```

```yaml
service: ergomotion_ksbt.dump_debug_state
```

If you have more than one configured bed, include `address` in the service data.

For live reverse-engineering, call `ergomotion_ksbt.set_debug_logging` with `enabled: true`, use the bed, then watch Home Assistant logs for raw and decoded notification output.

## Development notes

- Domain: `ergomotion_ksbt`
- Transport: Nordic UART Service
- Write UUID: `6e400002-b5a3-f393-e0a9-e50e24dcca9e`
- Notify UUID: `6e400003-b5a3-f393-e0a9-e50e24dcca9e`
- Reliable command prelude:
  1. `7102060680`
  2. wait `0.3s`
  3. `aa01000901210000020000d155`
  4. wait `1.0s`

