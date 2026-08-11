# Executive Summary: Lighting Instance Active Automations

Date: 2026-08-08
Instance: Home Light Controller (lighting_instance) · version 2026.7.4 · timezone America/New_York
Scope: 17 active automations (31 disabled)

## Overview

The lighting instance runs three cooperating automation layers. The **GPE (Global
Presence Engine)** computes who or what has *control intent* in each area and decides
which intent wins. The **UCC (Universal Controller Command)** layer converts physical
controller input (motion, switches, Pico remotes) into UCC event commands and steers
lights. The **System & support** layer provisions area profiles, reacts to sun phase
changes, keeps adaptive lighting and the Lutron registry in sync, and tracks lock
state.

All layers communicate over MQTT topics under `home/universal/bus` and coordinate
through shared registry sensors: `sensor.global_variable_registry`,
`sensor.presence_state_registry`, `sensor.device_lock_registry`, and
`sensor.schedule_posture`. Targets are selected through area/label intersects
(`override_eligible`, `area_override_eligible`) rather than hardcoded entity lists.

## GPE — Global Presence Engine (6 automations)

1. **Orchestrator V8.2** — Runs the claimant handshake: areas register intent via
   `sensor.presence_state_registry`, and the orchestrator resolves conflicts using
   the precedence stack (gatekeeper / ghost / veto). Hands off control with a 120
   second handover timer so transitions between claimants are smooth.
2. **Intent Distributor V3.5.0** — Takes the winning intent and distributes UCC
   command events. Priority order is strict: P3 schedule intents outrank P2 manual
   intents, which outrank P1 motion intents.
3. **Stateful Batching Janitor V3.2** — Cleans up expired tokens and stale state in
   `sensor.global_variable_registry` so batching state cannot leak between sessions.
4. **Area Context Synchronizer V1.5** — Pushes resolved area context and occupancy
   decisions into ESPHome profiles so device-level logic sees the same intent the
   automations see.
5. **Unified Gateway V6.0** — The single intake point for manual overrides
   (dashboard buttons, physical overrides routed to the bus). Every override enters
   GPE through this gateway, keeping the claimant model authoritative.
6. **Posture Override Reset V1 — "Smart Purge"** — When the house posture
   (`alarm_control_panel.house_posture_engine_house_posture`) changes, purges stale
   override claims so a new posture starts from a clean slate.

## UCC — Universal Controller Command (5 automations)

1. **light_call V5** — Resolves a UCC event into concrete light actions using a
   three-tier area/label intersect, hardware bucketing, and delta-checking so
   already-satisfied targets are skipped.
2. **Loopback Coordinator V3** — Implements native scene steering: relative
   brightness adjustments and posture-aware scene shifts. Commands loop back through
   the UCC bus to reuse light_call for the actual actuation.
3. **ESPHome Switch Coordinator V1.0** — Translates ESPHome press / double-press /
   hold gestures into UCC events. Button semantics are posture-aware.
4. **Lutron Pico V5.x** — Current Pico mapping using 500 ms / 250 ms gesture windows
   to disambiguate short presses from hold-to-dim.
5. **Lutron Pico V3.0 (legacy)** — Older Pico mapping retained for hardware that has
   not been re-paired; its press trigger is disabled, so only dim/steering gestures
   are processed.

## System & Support (6 automations)

1. **Area Profile Provisioning Engine V7.0** — Creates and maintains per-area device
   profiles (occupancy, default scene, allowed intents) referenced by GPE and UCC.
2. **Sun Phase Change Orchestrator V1** — Watches `sensor.schedule_posture` and
   re-evaluates lighting on sunrise/sunset transitions so schedules track real sun
   phase rather than fixed clock times.
3. **Adaptive Lighting Sync** — Bridges the adaptive lighting integration: syncs
   solar-based CCT and brightness changes into the GPE/UCC model using deadzones to
   avoid chatter on the bus.
4. **Lutron Registry Change Monitor** — Monitors the Lutron device registry and
   publishes `home/lutron/device_update` on the bus when devices are added, renamed,
   or removed, so maps stay current.
5. **remote_v2** — Zigbee2MQTT remote intake: translates remote button events into
   `select.<area>_matrix_scene` commands, with a queue capped at 10 to prevent
   event floods.
6. **Locked Indicator** — Reflects `sensor.device_lock_registry` state (powder room
   lock) onto an indicator so lock state is visible without polling the device.

## Relationship map

```
GPE (intent arbitration) ──► UCC (command execution) ──► lights
         │                              ▲
         │                              │
         └── System & support (profiles, sun phase, sync, registry, locks)
```

GPE owns *who may control*; UCC owns *how a command becomes light state*; System &
support keeps both layers' inputs (profiles, posture, registry, locks) current.
