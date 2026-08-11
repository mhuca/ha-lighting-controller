# **Universal Controller Command (UCC) \- Lutron Pico Coordinator Engine (v5.5)**

## **System Overview**

The **Lutron Pico Coordinator** is a local-first, high-performance gesture and intent engine for Home Assistant. It intercepts raw lutron\_caseta\_button\_event payloads, manages gesture timing (press, hold, double), resolves device hardware profiles and tag-based overrides, and dispatches standardized universal\_controller\_command events to downstream domain handlers.

Rebinding physical controls requires **zero YAML edits or service restarts**. Appending a functional tag word (e.g., Preset, Media, Feeder) to a device's name in the Lutron Mobile App instantly reconfigures its button mapping at runtime.

## **Key Architectural Principles**

1. **Self-Registering Override Tags**: Overrides are defined in a top-level dictionary (override). Tag matching dynamically extracts override.keys(), eliminating the need for hardcoded tag lists.  
2. **Exact Word/Token Stripping**: Device names are tokenized into discrete words before matching against tags. This prevents substring false-positives (e.g., preventing Intermediate from triggering media).  
3. **Deferred Command Resolution**: The base hardware map (command\_map) loads first. When a button event executes, cmd evaluates the override map (override\[matched\_tag\]) and falls back to command\_map if un-overridden.  
4. **Target Label Preservation**: Stripping an override tag slugifies the remaining string tokens while preserving trailing numbers for discrete target labels (e.g., Living Room Scene 1 Preset \-\> Tag: preset, Target Label: scene1).  
5. **Zero Dependency Overhead**: Per-device config lookups (e.g., sensor.pico\_config\_\<serial\>) and manual commissioning checks have been removed in favor of static dictionary evaluation.

## **Lutron App Naming & Tag Conventions**

To reconfigure a Pico, name the device in the Lutron App using the format:

\[Area/Zone\] \[Target Label\] \[Override Tag\]

| Lutron Device Name | Extracted matched\_tag | Resolved device\_name | Target Label | Applied Behavior |
| :---- | :---- | :---- | :---- | :---- |
| Living Room Main | *(none)* | main | \['main'\] | Base hardware profile (Light Call) |
| Kitchen Main Feeder | feeder | main | \['main'\] | Button 3 triggers pet feeder |
| Patio Main Media | media | main | \['main'\] | Play/Pause, Mute, Volume, Track Skip |
| Living Room Scene 1 Preset | preset | scene1 | \['scene1'\] | Sequenced scene cycles (max, 151, off, raise, lower) |

## **Data & Variable Resolution Pipeline**

\[ lutron\_caseta\_button\_event \]  
              │  
              ▼  
    1\. Lock Claim & Session Expiry Check  
              │  
              ▼  
    2\. Extract Base Config (by Pico Hardware Type)  
              │  
              ▼  
    3\. Match Tag Token (\`matched\_tag\` from \`override.keys()\`)  
       └── Tokenize \`raw\_device\_name\` \-\> Extract \`matched\_tag\`  
       └── Strip tag \-\> Resolve \`device\_name\` (Target Label)  
              │  
              ▼  
    4\. Wait for Release (500ms) \-\> Detect Hold vs Single/Double Press  
              │  
              ▼  
    5\. Resolve \`cmd\`:  
       └── Check \`override\[matched\_tag\]\[command\]\[button\]\`  
       └── Fallback to \`command\_map\[command\]\[button\]\`  
              │  
              ▼  
    6\. Fire \`universal\_controller\_command\` Event

## **Active Override Dictionaries**

### **1\. feeder**

* **Button 3 (press / hold)**: type: pet\_feeder, action: broadcast, value: portion

### **2\. media**

* **Button 2 (press)**: Media Play/Pause  
* **Button 3 (press)**: Volume Mute  
* **Button 4 (press)**: Next Track  
* **Button 5 (press / hold)**: Volume Up  
* **Button 6 (press / hold)**: Volume Down

### **3\. preset**

* **Button 2 (press)**: scene\_cycle \-\> max  
* **Button 3 (press)**: scene\_cycle \-\> 151 (Preset Favorite)  
* **Button 4 (press)**: scene\_cycle \-\> off  
* **Button 5 (press)**: scene\_cycle \-\> raise (Cycle Next Scene)  
* **Button 6 (press)**: scene\_cycle \-\> lower (Cycle Previous Scene)

## **How to Add a New Override Class**

To add a new override category (e.g., shade), add a new key dictionary under the override variable block:

      override:  
        shade:  
          press:  
            "2":  
              type: cover\_call  
              action: open  
              value: ""  
            "4":  
              type: cover\_call  
              action: close  
              value: ""

*No template or regex changes are required. Naming a device Bedroom Main Shade will automatically detect shade, strip the token, and map the custom shade actions.*

## **Complete Production Automation YAML (v5.5)**

alias: UCC \- Lutron Pico Coordinator \- Pico Registry Update (V5.5)  
description: \>-  
  High-performance gesture and intent engine for Lutron Picos (Flattened Architecture)  
triggers:  
  \- trigger: event  
    event\_type: lutron\_caseta\_button\_event  
    event\_data:  
      action: press  
    enabled: true  
conditions:  
  \- condition: template  
    value\_template: "{{ not is\_owned or is\_expired }}"  
actions:  
  \- event: device\_lock\_claim  
    event\_data:  
      device\_id: "{{ device\_id }}"  
      isOwned: true  
      owned\_ts: "{{ as\_timestamp(trigger.event.time\_fired) }}"  
  \- variables:  
      base\_pico\_configs:  
        Pico2Button:  
          press:  
            "1": {type: light\_call, action: turn\_on, value: max}  
            "5": {type: light\_call, action: turn\_on, value: min}  
        Pico3Button:  
          press:  
            "1": {type: light\_call, action: turn\_on, value: max}  
            "2": {type: light\_call, action: turn\_on, value: max}  
            "5": {type: light\_call, action: turn\_on, value: min}  
        PaddleSwitchPico:  
          press:  
            "2": {type: light\_call, action: turn\_on, value: ""}  
            "4": {type: light\_call, action: turn\_off, value: ""}  
          double:  
            "2": {type: light\_call, action: turn\_on, value: max}  
          hold:  
            "2": {type: light\_call, action: turn\_on, value: raise}  
            "4": {type: light\_call, action: turn\_on, value: lower}  
        Pico2ButtonRaiseLower:  
          press:  
            "2": {type: scene\_cycle, action: turn\_on, value: max}  
            "4": {type: scene\_cycle, action: turn\_on, value: "off"}  
            "5": {type: scene\_cycle, action: turn\_on, value: raise}  
            "6": {type: scene\_cycle, action: turn\_on, value: lower}  
          hold:  
            "5": {type: media\_call, action: broadcast, value: volume\_up}  
            "6": {type: media\_call, action: broadcast, value: volume\_down}  
        Pico3ButtonRaiseLower:  
          press:  
            "2": {type: light\_call, action: turn\_on, value: ""}  
            "3": {type: light\_call, action: turn\_on, value: ""}  
            "4": {type: light\_call, action: turn\_off, value: ""}  
            "5": {type: light\_call, action: turn\_on, value: raise}  
            "6": {type: light\_call, action: turn\_on, value: lower}  
          double:  
            "2": {type: light\_call, action: turn\_on, value: max}  
            "4": {type: light\_call, action: turn\_on, value: min}  
          hold:  
            "2": {type: light\_call, action: turn\_on, value: raise}  
            "4": {type: light\_call, action: turn\_on, value: lower}  
        Pico4Button2Group:  
          press:  
            "8": {type: light\_scene, action: main, value: "151"}  
            "9": {type: light\_scene, action: main, value: "off"}  
            "10": {type: light\_scene, action: front, value: "151"}  
            "11": {type: light\_scene, action: front, value: "off"}  
        Pico4ButtonScene:  
          press:  
            "8": {type: scene\_cycle, action: turn\_on, value: max}  
            "9": {type: scene\_cycle, action: turn\_on, value: raise}  
            "10": {type: scene\_cycle, action: turn\_on, value: lower}  
            "11": {type: scene\_cycle, action: turn\_on, value: "off"}  
      override:  
        feeder:  
          press:  
            "3": {type: pet\_feeder, action: broadcast, value: portion}  
          hold:  
            "3": {type: pet\_feeder, action: broadcast, value: portion}  
        media:  
          press:  
            "2": {type: media\_call, action: broadcast, value: media\_play\_pause}  
            "3": {type: media\_call, action: broadcast, value: volume\_mute}  
            "4": {type: media\_call, action: broadcast, value: media\_next\_track}  
            "5": {type: media\_call, action: broadcast, value: volume\_up}  
            "6": {type: media\_call, action: broadcast, value: volume\_down}  
          hold:  
            "5": {type: media\_call, action: broadcast, value: volume\_up}  
            "6": {type: media\_call, action: broadcast, value: volume\_down}  
        preset:  
          press:  
            "2": {type: scene\_cycle, action: turn\_on, value: max}  
            "3": {type: scene\_cycle, action: turn\_on, value: "151"}  
            "4": {type: scene\_cycle, action: turn\_on, value: "off"}  
            "5": {type: scene\_cycle, action: turn\_on, value: raise}  
            "6": {type: scene\_cycle, action: turn\_on, value: lower}  
  \- variables:  
      device\_id: "{{ trigger.event.data.device\_id | default('none') }}"  
      type: "{{ trigger.event.data.type | default('Pico3ButtonRaiseLower') }}"  
      serial: "{{ trigger.event.data.serial | default(0) }}"  
      command\_map: "{{ base\_pico\_configs.get(type, base\_pico\_configs\['Pico3ButtonRaiseLower'\]) }}"  
      session\_id: "{{ trigger.event.context.id | default('none') }}"  
      button\_number: "{{ trigger.event.data.button\_number | default(0) }}"  
      target\_area: "{{ area\_id(device\_id) | default(none) }}"  
      override\_tags: "{{ override.keys() | list }}"  
      raw\_device\_name: "{{ (trigger.event.data.device\_name | default('', true)) | lower }}"  
      matched\_tag: \>-  
        {% set tokens \= raw\_device\_name.replace('\_', ' ').split() %}  
        {{ (override\_tags | select('in', tokens) | list | first) | default('', true) }}  
      is\_overridden: "{{ matched\_tag \!= '' }}"  
      device\_name: \>-  
        {% set cleaned \= raw\_device\_name | replace(matched\_tag, '') %}  
        {{ cleaned | trim | slugify | default('main') }}  
  \- wait\_for\_trigger:  
      \- event\_type: lutron\_caseta\_button\_event  
        event\_data:  
          serial: "{{ serial }}"  
          device\_id: "{{ device\_id }}"  
          button\_number: "{{ button\_number }}"  
          action: release  
        trigger: event  
    timeout: "00:00:00.500"  
    continue\_on\_timeout: true  
    alias: Wait for Release Within 500ms  
  \- variables:  
      is\_hold: "{{ wait.trigger is none }}"  
  \- choose:  
      \- conditions:  
          \- condition: template  
            value\_template: "{{ not is\_hold }}"  
        sequence:  
          \- wait\_for\_trigger:  
              \- event\_type: lutron\_caseta\_button\_event  
                event\_data:  
                  serial: "{{ serial }}"  
                  device\_id: "{{ device\_id }}"  
                  button\_number: "{{ button\_number }}"  
                  action: press  
                trigger: event  
            timeout: "00:00:00.250"  
            continue\_on\_timeout: true  
    alias: If not hold wait 250ms for second press  
  \- variables:  
      command: "{{ 'hold' if is\_hold else ('double' if wait.trigger is not none else 'press') }}"  
      cmd: \>-  
        {% set base\_cmd \= command\_map.get(command, {}).get(button\_number | string, none) %}  
        {% set override\_cmd \= override.get(matched\_tag, {}).get(command, {}).get(button\_number | string, none) %}  
        {{ override\_cmd if (is\_overridden and override\_cmd is not none) else base\_cmd }}  
  \- if:  
      \- condition: template  
        value\_template: "{{ cmd is not none }}"  
    then:  
      \- variables:  
          is\_eligible: "{{ target\_area in label\_areas('area\_override\_eligible') }}"  
          intent\_type: \>-  
            {{ 'override' if is\_eligible and cmd.type \== 'light\_call' and cmd.action in \['turn\_on', 'turn\_off'\] else '' }}  
          domain: \>-  
            {{ {'light\_call': 'lighting', 'scene\_cycle': 'lighting', 'fan\_call': 'ventilation', 'media\_call': 'media'}.get(cmd.type, 'lighting') }}  
          profile\_sensor: sensor.{{ target\_area }}\_profile  
          profile\_exists: "{{ states(profile\_sensor) not in \['unknown', 'unavailable'\] }}"  
          profile\_features: \>-  
            {{ state\_attr(profile\_sensor, 'features') | default({}, true) if profile\_exists else {} }}  
          g\_env: \>-  
            {% set registry \= state\_attr('sensor.global\_variable\_registry', 'vars') | default({}, true) %}  
            {{ registry.get('globals', {}).get('environmental', {}) }}  
          current\_posture: \>-  
            {{ states(g\_env.get('schedule\_posture', '')) | default('daylight', true) }}  
          use\_night: \>-  
            {{ profile\_features.get('night\_light', false) and is\_state(g\_env.get('night\_posture\_sensor', ''), 'on') }}  
          target\_label: |-  
            {{ \['night\_light'\] if use\_night else \[device\_name\] }}  
      \- choose:  
          \- conditions:  
              \- condition: template  
                value\_template: "{{ command \== 'hold' }}"  
            sequence:  
              \- variables:  
                  repeat\_delay: "{{ 125 if cmd.type \== 'media\_call' else 500 }}"  
                  max\_iterations: "{{ (9 / (repeat\_delay / 1000)) | round(0) }}"  
              \- repeat:  
                  until:  
                    \- condition: template  
                      value\_template: "{{ repeat.index \> max\_iterations }}"  
                  sequence:  
                    \- event: universal\_controller\_command  
                      event\_data:  
                        source\_device: pico  
                        action\_type: "{{ cmd.type }}"  
                        action\_value: "{{ cmd.value }}"  
                        command\_input: "{{ cmd.action }}"  
                        target:  
                          area\_id: "{{ target\_area }}"  
                          label\_id: "{{ target\_label }}"  
                        session\_id: "{{ session\_id }}"  
                        metadata:  
                          session\_id: "{{ session\_id }}"  
                          claimant\_id: \>-  
                            pico.{{ \[trigger.event.data.area\_name | default('unknown', true), trigger.event.data.device\_name | default('device', true)\] | slugify }}  
                          publish\_intent: ignore  
                        command: "{{ command }}"  
                        command\_type: \>-  
                          {{ trigger.event.data.button\_type | slugify \~ '\_' \~ command }}  
                    \- delay:  
                        milliseconds: "{{ repeat\_delay }}"  
            alias: Hold \- Repeat fire events  
        default:  
          \- event: universal\_controller\_command  
            event\_data:  
              source\_device: pico  
              action\_type: "{{ cmd.type }}"  
              action\_value: "{{ cmd.value }}"  
              command\_input: "{{ cmd.action }}"  
              target:  
                area\_id: "{{ target\_area }}"  
                label\_id: "{{ target\_label }}"  
              metadata:  
                session\_id: "{{ session\_id }}"  
                claimant\_id: \>-  
                  pico.{{ \[trigger.event.data.area\_name | default('unknown', true), trigger.event.data.device\_name | default('device', true)\] | slugify }}  
                seconds: "{{ 7200 if cmd.action \== 'turn\_on' else 0 }}"  
                publish\_intent: \>-  
                  {{ 'ignore' if not is\_eligible else 'add' if cmd.action \== 'turn\_on' else 'remove' }}  
                intent\_type: "{{ intent\_type }}"  
                domain: "{{ domain }}"  
              command: "{{ command }}"  
              command\_type: \>-  
                {{ trigger.event.data.button\_type | lower | replace(' ', '') | replace('\_', '') }}\_{{ command }}  
          \- action: logbook.log  
            data:  
              name: UCC\_SENT  
              message: \>-  
                Area: {{ target\_area }} | Action: {{(cmd.type) }} | Value: {{(cmd.value) }} | Label: {{ target\_label\[0\] }}  
              entity\_id: sensor.ucc\_registry\_log  
  \- event: device\_lock\_claim  
    event\_data:  
      device\_id: "{{ device\_id }}"  
      isOwned: false  
      owned\_ts: "{{ as\_timestamp(now()) }}"  
mode: parallel  
variables:  
  session\_id: "{{ trigger.event.context.id }}"  
  sessions: \>-  
    {{ state\_attr('sensor.device\_lock\_registry', 'active\_sessions') | default({}) }}  
  device\_id: "{{ trigger.event.data.device\_id | default('none') }}"  
  session: "{{ sessions.get(device\_id, {}) }}"  
  is\_owned: "{{ session.isOwned | default(false) }}"  
  start\_ts: "{{ as\_timestamp(trigger.event.time\_fired) | default(as\_timestamp(now())) }}"  
  is\_expired: "{{ start\_ts \>= (session.expiry | default(0)) }}"  
max: 10  
