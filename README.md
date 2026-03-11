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
* **Safe Discovery:** New devices default to `uninitialized`, preventing accidental switching until a user first interacts with the device.

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
