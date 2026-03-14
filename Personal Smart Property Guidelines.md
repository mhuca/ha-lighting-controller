context: Home Assistant GPE Governance framework: PSPG (Policy, Standard, Procedure, Guideline) agent\_instruction: "Prioritize Situation-based recovery. Use 'Lean Instance' logic. Refer to S-01 for occupancy conflicts."

# **📘 Personal Smart Property Guidelines (PSPG)**

## **⚡ Situation: Quick-Response Index**

\<\!-- meta: { "type": "index", "purpose": "routing" } \--\>

* **Door opened, but lights didn't pre-heat:** See \[PR-03\]  
* **Working in a room and lights went out:** See \[S-01\]  
* **Adding a new camera or motion sensor:** See \[S-03\]  
* **Debugging a Fan or Closet Janitor:** See \[PR-04\]

# **1\. Standards (The "Must")**

## **\[S-01\] The Enclosure Standard**

\<\!-- meta: { "id": "std\_occupancy\_001", "remedy": "install\_presence\_hardware" } \--\>

**Standard:** Any area where a door can be closed behind a person (occupiable space) MUST have a dedicated presence sensor (PIR/mmWave).

**Exemptions:** Transient storage areas such as closets, cabinets, or pantries are exempt from this requirement, as these are typically governed by simple door-state logic.

**Logic:** Without presence hardware, the system defaults to a 5-second "Transient" timer upon door closure.

## **\[S-03\] Perimeter Logic Intersection (V2.0)**

\<\!-- meta: { "id": "std\_logic\_002", "logic": "intersection" } \--\>

**Standard:** Outdoor presence is valid ONLY when a person label intersects with an area label AND the house is in "Night Posture."

**Implementation:** (label:person) ∩ (label:area) | filter:night\_posture.

**Safety:** Uses a 2-minute delay\_off to account for transient AI detection drops.

## **\[S-04\] The Logbook Dictionary**

**Standard:** All GPE events must be logged using the following schema to ensure rapid diagnostics without "log flooding."

| Message Header | Level | Context |
| :---- | :---- | :---- |
| **STATE: LOCKED** | INFO | Confirmed presence; Reaper is blocked. |
| **STATE: RESET** | DEBUG | Registry timer refreshed (includes Door Age). |
| **TYPE: Motion** | INFO | Triggered by PIR/mmWave. |
| **TYPE: Portal** | INFO | Triggered by door/entrance sensor. |

# **2\. Procedures (The "How")**

## **\[PR-01\] New Area Onboarding**

\<\!-- meta: { "id": "proc\_new\_area" } \--\>

1. **Label Area:** Add night\_light to the HA Area settings.  
2. **Create Master:** Create binary\_sensor.\[area\]\_presence\_master.  
3. **Tag Sensor:** Apply the presence label to the Master sensor.

## **\[PR-03\] Portal "Pre-Heat" Setup**

\<\!-- meta: { "id": "proc\_portal\_preheat" } \--\>

**Situation:** Want lights on as you open the door, not after camera detection. **Action:** Apply the entrance label to the door's binary sensor. **Effect:** Grants 10s buffer for camera/logic latency.

## **\[PR-04\] Janitor V1.0 Compliance**

\<\!-- meta: { "id": "proc\_janitor\_compliance" } \--\>

When deploying a new Janitor device (Fans/Closets):

1. **Package:** Ensure device\_base.yaml is included.  
2. **Version:** Set version: "1.0" in the project block.  
3. **Handshake:** Verify area\_key matches the HA Area underscore convention.  
4. **Kill-Switch:** Set skip\_warning: "true" for instant-off hardware.

# **⚠️ Compliance Hit-List (Spring Clean)**

| Area | Issue | Standard | Status |
| :---- | :---- | :---- | :---- |
| **Powder Room** | Janitor Handshake | PR-04 | ✅ Verified (v1.0) |
| **Backyard** | Logic Intersection | S-03 | ✅ Verified |
| **Mud Room** | Entrance Label | PR-03 | ✅ Verified |
| **Server Room** | No Presence Sensor | S-01 | ❌ Non-Compliant |
| **Panel Room** | No Presence Sensor | S-01 | ❌ Non-Compliant |

