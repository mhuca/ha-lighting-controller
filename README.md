# **🏠 Home Assistant: Lean Logic OS**

**Goal:** A label-driven, hardware-agnostic automation engine that prioritizes modularity over hard-coded entities.

## **⚡ Quick-Start: Onboarding a New Area**

To bring a new room into the **GPE (Global Presence Engine)**, follow these steps:

1. **Area Setup:** Create the Area in HA and apply the night\_light label.  
2. **Master Sensor:** Create a template sensor binary\_sensor.\[area\]\_presence\_master.  
3. **Tagging:** Apply the presence label to the Master sensor.  
4. **Perimeter Safety:** Tag doors with entrance to enable "Pre-heat" logic (10s lead time).

## **🧠 Core Implementation Patterns**

### **1\. The Safety Fetch (Registry Pattern)**

Always wrap registry calls in this safety check. It prevents your logic from "failing upward" or crashing if the registry sensor is temporarily unavailable during a reboot.

\# Pattern: Global Context Fetch  
variables:  
  r: "{{ state\_attr('sensor.global\_variable\_registry', 'vars') }}"  
  \# Safety Guard: Stop execution if registry is null  
  guard: "{{ r is none }}"

### **2\. The Intersection Rule (Perimeter Security)**

For outdoor zones (Backyard/Front Porch), we use a "Logic Sandwich" to eliminate ghost triggers from wind or shadows.

* **Trigger:** Person (Object) ∩ Physical Area (Zone) \= **Valid Presence**.  
* **Verification:** Use the label\_entities filter to verify the intersection in the Developer Tools.

## **🎭 The Logic Stack**

* [**PSPG.md**](https://www.google.com/search?q=./PSPG.md): Governance, Standards, and Compliance Hit-lists.  
* [**ARCHITECTURE.md**](https://www.google.com/search?q=./ARCHITECTURE.md): Technical breakdown of the Registry, Orchestrator, and Reaper.

\<\!-- machine\_intent: { "role": "root\_documentation", "framework": "lean\_instance\_v2" } \--\>