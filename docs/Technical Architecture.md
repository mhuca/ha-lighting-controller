# **🏗️ Technical Architecture: The Three Pillars**

**Description:** This document defines the high-level logic flow and core structural components of the Lean Logic OS. It serves as the blueprint for understanding how the system coordinates intent, hardware, and state management.

## **📝 System Purpose**

The Architecture Deep-Dive is designed to maintain a hardware-agnostic logic layer. By decoupling "Intent" from "Execution," the system ensures that changes to physical devices do not require a rewrite of core home intelligence.

## **1\. The Global Variable Registry**

The sensor.global\_variable\_registry acts as the **Single Source of Truth (SSoT)**.

* **Role:** Centralizes all hard-coded entity IDs, environmental postures, and service call targets.  
* **Benefit:** If you swap a smart plug or a Lutron bridge, you update it in the registry once, and every automation in the house inherits the change.

## **2\. The GPE Orchestrator (The Brain)**

The Presence Orchestrator is a single, label-driven automation that handles intent.

* **Triggers:** Any entity with labels presence, entrance, or door.  
* **Decision Logic:** \* If entrance \+ on \-\> Pre-heat Area.  
  * If door \+ off \+ no\_presence \-\> Start 5s Transient Timer.  
  * If presence \+ off \-\> Start 30s Registry Expiry.

## **3\. The Universal Controller Command (The Muscle)**

The lighting\_controller (or UCC) is the execution layer. It decouples **intent** from **hardware**.

* **Standardization:** Instead of automations calling light.turn\_on, they send a command to the UCC with an area\_id and action\_type.  
* **Intelligence:** The UCC checks the house\_posture (Day vs. Night) to decide if it should fire a 100% brightness scene or a 10% "Night Light" scene.

## **4\. Lutron Pico: Registry Integration**

To maintain a "Lean Instance," physical switches like the Lutron Pico do not trigger lights directly.

* **Pattern:** Button presses update a specific pico\_registry\_state inside the Global Registry.  
* **Flow:** Pico Press \-\> Update Registry \-\> Orchestrator detects change \-\> UCC executes.

## **5\. Occupancy vs. Vacancy Logic**

The system distinguishes between "Is someone there?" (Occupancy) and "Is the room empty?" (Vacancy).

* **The Lock:** If presence is detected, the area is "Locked." No timers can expire.  
* **The Release:** Timers only start when the area is confirmed "Vacated" or a "Master Reset" is triggered, ensuring the house never "fights" the resident.

## **6\. The Recursive Reaper (The Cleaner)**

The "Cleaner" is the background process that enforces the Registry Expiry.

* **The Sweep:** Every 5 minutes (or on event), it checks sensor.lighting\_off\_registry.  
* **The Warning:** If an area is nearing expiry, it triggers the "Dim Warning" unless the area is lock\_eligible.  
* **The Veto:** If a presence sensor is active or an OVERRIDE is set, the Reaper is forced to skip the sweep for that area.

## **7\. The "Janitor" Pattern (Edge Logic V1.0)**

The Janitor Pattern allows localized hardware to negotiate its own expiry with the central Reaper.

* **Layered Logic:** Devices utilize a common/device\_base.yaml for internal ticking (local safety) and a localized YAML for HA Handshakes.  
* **The Hand-off:** Upon a hardware on\_turn\_off event, the device sends a timestamp and skip\_warning flag to the Home Assistant Registry.  
* **The Immediate Reaper:** A 500ms delay is followed by a forced esphome.start\_registry\_cleaner event, ensuring the Reaper processes the 5-second kill timer without waiting for the 5-minute sweep.  
* **Legacy Cleanup:** V1.0 removes manual timer\_entity\_id selection in favor of automatic area\_key mapping.

## **8\. The Intersection Rule (Perimeter Security V2.0)**

Standard for Outdoor Zones: Prevents false positives by requiring a logical "AND" between disparate sensory inputs.

* **The Logic:** (label:person) ∩ (label:back). This ensures that person detection is localized specifically to the target area before triggering.  
* **Environmental Gating:** Presence is only considered "Active" if the house\_is\_in\_night\_posture is true. This prevents unnecessary high-intensity logic during daylight hours when visibility is high.  
* **Modularity:** By using label\_entities, the system is hardware-agnostic. Adding a new AI camera or a localized mmWave sensor only requires applying the correct labels in the Home Assistant UI.  
* **State Resilience:** Uses a delay\_off: minutes: 2 to account for "motionless" presence (e.g., someone standing still in a dark corner) where AI detection might briefly drop.

\<\!-- machine\_intent: { "role": "technical\_reference", "architecture\_version": "3.2" } \--\>