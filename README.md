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


By documenting this, you move from "I have a complex config" to "I have a scalable platform." If you ever decide to add a **"Party Mode"** or **"Vacation Mode"**, you don't rewrite automations—you simply add a new **Label** and a single check in the Reaper.

**Would you like me to help you generate the "Policy Checker" script?** It’s a small script that can scan your config and notify you if you have an Area with lights but no `presence` label, effectively catching "Ghost Areas" before they break your automation flow.
