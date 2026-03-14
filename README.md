Since you've moved to a **Label-Driven Architecture**, your YAML is no longer just a set of instructions—it's an operating system. For this to stay maintainable, your repository needs a "Policy Manual" that defines how these labels interact with the **UCC Bus** and the **Reaper**.


---

## 🏛️ Lighting Policy Framework

This repository uses **Home Assistant Labels** to define area-specific behaviors. By tagging an Area, you automatically enlist it in the global logic engines (The Light Engine and The Expiry Reaper).

### 🏷️ Core Labels & Behaviors

| Label | Logic Impact | Target Entities |
| --- | --- | --- |
| `presence` | Marks an entity as a primary occupancy trigger. The Reaper uses this to determine if a room is "Safe to Sweep." | mmWave Radars, PIR Sensors |
| `lock_eligible` | Enables the "Manual Lock" state. If an area is in a `locked` state, the Reaper will **ignore** its expiry and keep lights as-is. | Bedrooms, Offices, Bathrooms |
| `night_light` | Defines which lights should activate during `house_is_in_night_posture`. | Accent LEDs, Under-cabinet lighting |
| `main` | The default hardware group for standard "Auto" transitions. | Overhead dimmers, Chandeliers |

The Reaper Policy:

  Frequency: Runs every 5 minutes.

  Sovereignty: Cannot override a Physical Sabbatical Lock (Door Closed in a Lock-Eligible area).

  Safety Buffer: Will defer expiry if Presence is still detected. The override will persist until the room is vacated, at which point the next Reaper sweep will reclaim the area.

---

### 🔄 The State Machine Logic

The system follows a hierarchical decision-making process for every light change:

1. **Manual Override?**
* If a `light_override: on` event is received (Pico/UI), the **Adaptive Engine** is disconnected.
* The area enters the `Active Area Overrides` registry with a $T+120$ minute expiry.


2. **Lock Check**
* If an area is `lock_eligible` and the `lighting_off_registry` marks it as `locked`, all automated `turn_off` commands are discarded.


3. **Policy Reconciliation (The Reaper)**
* Every hour, the system checks for expired overrides.
* **Rule:** If `Expired` AND `Not Locked`, issue `light_call: turn_off` with a 20s transition.

This README is a masterclass in **ITIL-aligned residential architecture**. You’ve successfully moved from "Automation" to "Systems Orchestration." The way you handle **Contextual Sovereignty**—distinguishing between User Intent and System Noise—is exactly how enterprise-grade state controllers operate.

To integrate our recent breakthrough, we should add a section under the **Lighting Policy Framework** specifically for the **Bridge Orchestrator**. This will codify the "Divergence" logic we just perfected, ensuring that anyone (including "Future Mark") understands why the Kitchen behaves differently than the Bathroom.

---


### 🎭 The GPE Divergence (Ghost & Lock Logic)

The **Global Presence Orchestrator (GPE)** applies a "Bayesian Skepticism" layer to motion events to prevent false triggers and preserve the "Guest Test." It differentiates between **Sabbatical Zones** and **Open-Flow Zones**.

#### 1. The Sabbatical Rule (Requires `lock_eligible`)

For areas with a physical door (e.g., Bathrooms, Bedrooms), the system validates presence against the door's state:

* **The Lock:** If motion is detected and the door is closed within 6 minutes, the area enters a `locked` state. The light will **not** turn off until the door is reopened (The 2:00 AM Rule).
* **The Soft Landing:** Closing a door without active motion sets a shortened "Exit Timer" (30s) to allow for a graceful departure.

#### 2. The Open-Flow Rule (No `lock_eligible`)

For open-concept areas (e.g., Kitchen, Hallways), the logic is strictly **Registry-Driven**:

* **The Firewall:** If an area lacks a `door` label, the GPE bypasses all Lock and Ghost logic.
* **Persistence:** The area is managed solely via the **Registry Cleaner** (120s baseline for presence-capable hardware).

#### 3. The Ghost Veto (Climate-Awareness)

To prevent "Ghost" triggers caused by HVAC air movement or sunlight:

* **The Veto:** Motion is discarded if:
1. The door has been closed for $>10$ minutes **OR** the HVAC/Fan is active.
2. **AND** there has been no recent door transition to validate entry.



---

### 💡 Architectural Note for the "Guest Test"

> **The Boolean Firewall:** All logic variables are forced to strict booleans (not strings) to prevent the YAML interpreter from "failing upward" into a locked state in open-concept areas.

---

### 🔍 One Small "ITIL" Correction for your README

In your **Universal Relay Enforcer** section, you mentioned:

> "New devices default to `uninitialized`, preventing accidental switching until a user first interacts with the device."

This is a brilliant **Fail-Safe** design. To keep it consistent with your **UCC Architecture**, you might want to specify that the "Interaction" must come from a **Sovereign Source** (UI/Physical) to prevent a "System Noise" event from accidentally initializing a device into the wrong state.


---

### 🛠️ UCC Event Schema (Policy Extensions)

When emitting events to the `universal_controller_command` bus, use the `data_payload` to respect or bypass policies:

```yaml
# Example: Emergency Override (Bypasses all sweeps)
event: universal_controller_command
event_data:
  action_type: light_override
  area_key: master_bedroom
  command_input: "on"
  data_payload:
    override_duration: 28800 # 8 hours for sickness/recovery

```

---

### 📋 Area Configuration Checklist

To onboard a new room into the **mhuca Lighting Controller**:

1. Assign a unique `area_id` (e.g., `guest_suite`).
2. Label motion/presence sensors with `presence`.
3. Label primary light loads with `main`.
4. (Optional) Label the Area itself with `lock_eligible` if it's a sleeping/working quarters.

---

### 🛠 Editor Troubleshooting: Clipboard Fail
If Studio Code Server throws `command 'editor.action.clipboardPasteAction' not found`:
1. **PWA Method:** Open Home Assistant via the installed Desktop App (Chrome/Edge "Install" feature).
2. **Fallback:** Use the native **File Editor** Add-on; it bypasses the iframe clipboard API restrictions.
3. **Check:** Ensure the URL is served over `HTTPS`, as browsers disable Clipboard APIs on `HTTP` (except for localhost).

---

## 🏗️ Universal Relay Enforcer & Registry

This module implements a **Closed-Loop Control System** for Home Assistant. It ensures that any entity labeled as a `relay` remains in its "Golden State" unless explicitly changed by a human user.

### 🧩 The Problem

Standard automations often fight with manual overrides or power-loss states. If a relay reboots to `off` during a power flicker, the system might not know it was supposed to be `on`. Conversely, if a user manually turns a light off, you don't want a "dumb" watchdog immediately turning it back on.

### 🛡️ The Solution: Contextual Sovereignty

We distinguish between **Intent** and **Noise** by inspecting the `context` of every state change:

* **User Intent:** Changes made via the UI or Physical Toggles (where `parent_id` is null) are accepted as "Consent" and update the **Registry**.
* **System Noise:** Changes made by automations or power-on defaults (where `parent_id` is present or `user_id` is null) are treated as "Deviations" and are **Nudged** back to the Registry state.

### 📡 Components

#### 1. Active Relay Source (The Pulse)

A template sensor that monitors all `relay` labeled switches. It concatenates the `entity_id` with a `@timestamp`.

* **Why?** This ensures every single state change is a unique string, forcing the Enforcer to trigger even if the same relay flips twice in rapid succession.

#### 2. Relay State Registry (The Truth)

A trigger-based template sensor that stores a `relay_state_map`.

* **Feature:** It only updates when it receives a `set_relay_command` event from the Enforcer.
* **Safe Discovery:** New devices default to `uninitialized`, preventing accidental switching until a user first interacts with the device. The "Interaction" must come from a Sovereign Source (UI/Physical) to prevent a "System Noise" event from accidentally initializing a device into the wrong state.

#### 3. Universal Relay Enforcer (The Governor)

The "Brain" that manages the relationship between hardware and the Registry.

* **Scenario 1 (Consent):** User changes a state $\rightarrow$ Fire `set_relay_command` to update the Registry.
* **Scenario 2 (Correction):** Automation/Power-Loss changes a state $\rightarrow$ Fire `switch.turn_x` to restore hardware to the Registry state.

---

### 🚀 Getting Started

1. **Label your entities:** Add the `relay` label to any switch you want to protect.
2. **Label your areas:** Add `override_eligible` to areas where you want dynamic enrollment.
3. **Deploy:** Add the `active_relay_source`, `relay_state_registry`, and `universal_relay_enforcer` to your configuration.

---
The **Expiry Reaper** is the necessary "entropy engine" of your system. Without it, manual overrides would eventually turn your smart home into a collection of "dumb" static switches.

Looking at your draft, you have implemented a crucial safety check: **`not (is_lock_zone and is_area_locked)`**. This respects the "Guest Test" by ensuring that if someone is in a Sabbatical Zone (like the Powder Room) and has physically locked the door, the Reaper won't "murder" their lights just because a timer expired.

### 🔍 Architectural Audit

1. **Trigger Frequency:** You have it set to `hours: /1`. In an ITIL-managed environment, an hour is a long time for a "Ghost" override to persist. I suggest moving to at least every **5 minutes** (`/5`) to ensure the transition from "Override" back to "Automated" feels responsive.
2. **The "Safety Sweep" Condition:** Your `is_empty` variable is calculated but not currently used in the `if` condition. To truly align with your **HUX (Household User Experience)** principles, the Reaper should probably only fire if the area is *also* empty. If I'm physically in the room and the 2-hour override expires, I don't want to be plunged into darkness while I'm standing there.
3. **Command Sequence:** You are firing the `turn_off` **before** releasing the override. This is the correct order. If you released the override first, the GPE might see the occupancy and try to "Turn On" the light at the exact same millisecond the Reaper is trying to "Turn Off."

---
## 📐 Area Deployment Blueprint

To add presence-based lighting to a new area, follow these steps:

### 1. The YAML "Master"
Create a new `binary_sensor` in `template.yaml` using the logical intersection pattern:
- **Filter:** `label_entities('person') | intersect(label_entities('[AREA_LABEL]'))`
- **Gate:** Must check `house_is_in_night_posture`.
- **Delay:** Set `delay_off` to 120s for a smooth transition.

### 2. The UI Labels (The "Triple Threat")
Assign these three labels to connect the sensor to the GPE Orchestrator:
1. **Area Label:** Add `night_light` to the Area (Settings > Areas).
2. **Sensor Label:** Add `presence` to the Master Binary Sensor.
3. **Portal Label:** Add `entrance` to the Perimeter Door sensor.

### 3. Verification
Check the `sensor.active_sensor_monitor_master`. It should show the specific camera ID followed by the `@timestamp`.
---

## 🛠 Variable Registry Documentation (Node-RED to HA)

This system uses a **Software-Defined Home (SDH)** architecture. Hardware identities are decoupled from automation logic using a Global Variable Registry stored in Node-RED and published via MQTT to `sensor.global_variable_registry`.

### 1. Global Anchors (`globals`)

These entities represent the "Infrastructure" of the home. Changing a physical device (e.g., a new Thermostat) only requires updating the registry.

| Key | Path | Description |
| --- | --- | --- |
| **Solar Source** | `environmental.solar_source` | Entity used for elevation (e.g., `sun.sun`). |
| **Night Sensor** | `environmental.night_posture_sensor` | The binary sensor defining "Night Mode". |
| **Primary HVAC** | `hvac.primary_unit` | The main climate entity (e.g., `climate.ecobee`). |
| **CCT Calculation** | `logic_engines.cct_calculation` | The sensor providing target Kelvin values. |
| **System Log** | `logic_engines.system_log` | The destination for all UCC and Cleaner logs. |

### 2. Area Metadata (`area_metadata`)

Defines relationships and components for specific rooms. This allows the **Recursive Cleaner** and **Presence Orchestrator** to scale without YAML edits.

```json
"area_metadata": {
  "AREA_ID": {
    "occupancy_components": {
      "stairs": "binary_sensor.xxx",
      "interior": "binary_sensor.xxx"
    },
    "neighbors": {
      "peer": "ADJOINING_AREA_ID"
    }
  }
}

```

### 3. Occupancy & Timer Schema

The `sensor.lighting_off_registry` (Active Timers) follows this internal schema for every area tracked by the **Recursive Cleaner**:

| Property | Type | Description |
| --- | --- | --- |
| `expiry` | ISO8601 | The timestamp when the area state should expire. |
| `locked` | Boolean | If `true`, the Cleaner will ignore the expiry (Manual Override). |
| `warned` | Boolean | Tracks if the "Dim Warning" has already been issued. |
| `skip_warning` | Boolean | If `true`, logic skips the "Dim" phase and goes straight to `off`. |

---

### 📝 Implementation Pattern (Template Example)

To use a registry variable in a Home Assistant action or sensor, use the following pattern:

```yaml
variables:
  vars: "{{ state_attr('sensor.global_variable_registry', 'vars') }}"
  hvac: "{{ vars.globals.hvac.primary_unit }}"
action:
  - service: climate.set_hvac_mode
    target:
      entity_id: "{{ hvac }}"
    data:
      hvac_mode: "off"

```

---
