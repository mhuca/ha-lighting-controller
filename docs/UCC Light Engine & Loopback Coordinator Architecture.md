# **Universal Controller Command (UCC) \- Light Engine & Loopback Coordinator Architecture**

## **Executive Summary**

The Universal Controller Command (UCC) suite decouples hardware triggers (keypads, sensors, remotes) from downstream lighting execution. The architecture consists of two primary operational components:

1. **UCC Light Engine (UCC \- Light Call V5.0)**: Resolves targeted area entities using label intersection filtering, sorts devices into capability buckets (CCT, dimmer, binary, standard), performs traffic-reducing delta checks, and executes direct hardware service calls or scene recalls.  
2. **UCC Loopback Coordinator (UCC \- Loopback Coordinator V3.0)**: Manages posture-aware scene shifting, UI selector synchronization, relative steering (raise, lower, next, previous), and native scene invocation.

## **1\. UCC Light Call Engine (v5.0)**

### **Architectural Principles**

* **Three-Tier Intersection Engine**: Resolves physical targets via area\_entities(target\_area) | intersect(target\_labels). This ensures intent-driven filtering (e.g., turning on Ambient lights in the Kitchen) without hardcoding entity IDs.  
* **Hardware Capability Bucketing**: Sorts matched entities into distinct execution groups based on capability attributes (color\_temp, supported\_color\_modes, max\_color\_temp\_kelvin) to prevent runtime service call errors.  
* **Delta Checking**: Compares current brightness/Kelvin values against target values before dispatching service calls. Commands are suppressed unless ![][image1] or ![][image2], eliminating unnecessary network congestion and "popcorning" on Zigbee/Z-Wave networks.

### **Hardware Capability Buckets**

| Bucket Name | Criteria & Filters | Executed Action / Data Payload |
| :---- | :---- | :---- |
| **IKEA CCT** | max\_color\_temp\_kelvin \<= 4000 & color\_temp in supported modes | Clamps Kelvin to \[2202, 4000K\] ceiling; updates color\_temp\_kelvin \+ brightness |
| **Standard CCT** | Standard tunable white bulbs (color\_temp supported) | Clamps Kelvin to bulb hardware limits; updates color\_temp\_kelvin \+ brightness |
| **Dimmer Lights** | Entity matches label\_entities('CurrentCTDimmer') | Updates brightness using global calculated dimmer level |
| **Binary Lights** | supported\_color\_modes \== \['onoff'\] & current state off | Calls light.turn\_on with no color/brightness parameters |
| **Standard Lights** | Fallback for remaining single-channel/dimmable lights | Updates brightness or brightness\_step based on input command |

## **2\. UCC Loopback Coordinator Engine (v3.0)**

### **Architectural Principles**

* **Posture-Aware Scene Shifting**: Evaluates the global posture sensor (disarmed, armed\_night, armed\_away) and applies an index offset (e.g., \+0 for disarmed, \+5 for night) to shift requested scene IDs dynamically without altering input commands.  
* **Relative Steering & Alias Navigation**: Accepts relative inputs (next, previous, raise, lower, max, min, restore) and maps them against sorted, available scene entities in the target area.  
* **UI Selector Synchronization**: Publishes JSON payloads over MQTT to retain and sync state across Home Assistant UI scene selectors (select.\<area\>\_matrix\_scene).

## **Data Pipeline Diagram**

\[ Input Trigger: Event / MQTT / Select Change \]  
                       │  
                       ▼  
            1\. Payload Extraction  
        (Area ID, Target Labels, Scene ID)  
                       │  
        ┌──────────────┴──────────────┐  
        ▼                             ▼  
\[ Direct Light Call \]         \[ Scene Call \]  
        │                             │  
        ▼                             ▼  
2\. Area/Label Intersect       2\. Posture Offset Mapping  
        │                        (disarmed: \+0, night: \+5)  
        ▼                             │  
3\. Hardware Bucketing                 ▼  
   \- IKEA CCT                 3\. Scene Entity Resolution  
   \- Standard CCT                (^scene.\<area\>\_\<shifted\_id\>\_)  
   \- Dimmer / Binary / Standard       │  
        │                             ▼  
        ▼                     4\. Execute \`scene.turn\_on\`  
4\. Delta Check Suppression            │  
        │                             ▼  
        ▼                     5\. MQTT UI State Sync  
5\. Parallel \`light.turn\_on\`      (\`select.\<area\>\_matrix\_scene\`)

## **Production Automation YAML: UCC Light Call V5.0**

alias: UCC \- Light Call V5  
description: \>-  
  Target intersection engine, capability bucketing, and delta-checked lighting coordinator.  
triggers:  
  \- trigger: event  
    id: UCC\_Event  
    event\_type: universal\_controller\_command  
    event\_data:  
      action\_type: light\_call  
    enabled: true  
  \- trigger: event  
    id: eUCC\_Event  
    event\_type: esphome.universal\_controller\_command  
    event\_data:  
      action\_type: light\_call  
    enabled: false  
  \- trigger: mqtt  
    id: MQTT\_Message  
    options:  
      topic: home/universal/bus  
      payload: light\_call  
      value\_template: "{{ value\_json.action\_type }}"  
    enabled: false  
conditions: \[\]  
actions:  
  \- alias: Intent and Context  
    variables:  
      target\_kelvin: |  
        {% set registry \= state\_attr('sensor.global\_variable\_registry', 'vars') | default({}, true) %}  
        {% set g\_logic \= registry.get('globals',{}).get('logic\_engines',{}) %}  
        {{ states(g\_logic.get('cct\_calculation', 3200)) | int }}  
      target\_color\_temp: "{{ 1000000/target\_kelvin | round(0) | int }}"  
      target\_br\_dimmer: |  
        {% set registry \= state\_attr('sensor.global\_variable\_registry', 'vars') | default({}, true) %}  
        {% set g\_logic \= registry.get('globals',{}).get('logic\_engines',{}) %}  
        {{ states(g\_logic.brightness\_calculation) | int(255) }}  
      log\_dest: |  
        {% set registry \= state\_attr('sensor.global\_variable\_registry', 'vars') | default({}, true) %}  
        {% set g\_logic \= registry.get('globals',{}).get('logic\_engines',{}) %}  
        {{ g\_logic.get('system\_log','') }}  
      payload: \>-  
        {{ trigger.payload if trigger.id \== 'MQTT\_Message' else trigger.event.data }}  
      action\_val: "{{ payload.action\_value | default('') }}"  
      val: "{% set t \= payload.get('target', {}) %} {{ t.get('label\_id', \[\]) }}"  
      target\_labels: |  
        {{ ( \[val\] if val is string else val)   
          | map('label\_entities')   
          | sum(start=\[\])   
          | unique   
          | list   
        }}  
      target\_area: |-  
        {% set t \= payload.get('target', {}) %}   
        {{ t.get('area\_id', payload.get('area\_key','none')) }}  
      target\_scene: |-  
        {% set t \= payload.get('target', {}) %}   
        {{ t.get('scene\_id', \-1 ) }}  
      meta: "{{ payload.get('metadata', {}) }}"  
      action\_type: \>  
        {{ 'turn\_off' if payload.get('action\_value', '') in \[0,'0','off'\] else payload.get('command\_input', 'turn\_on') }}  
      current\_posture: |  
        {% set registry \= state\_attr('sensor.global\_variable\_registry', 'vars') | default({}, true) %}  
        {% set g\_env \= registry.get('globals', {}).get('environmental', {}) %}  
        {{ states(g\_env.get('home\_posture', '') ) | default('disarmed') }}  
  \- variables:  
      relays: \>-  
        {{ \[\] if payload.area\_context is not defined else payload.get('area\_context', {}).get('profile\_topography',{}).get('relay\_entities',\[\]) }}  
      turn\_on\_relay: \>  
        {{ true if payload.area\_context is defined and relays | count \> 0 and is\_state( relays | first, 'off') else false }}  
  \- if:  
      \- condition: template  
        value\_template: "{{ turn\_on\_relay }}"  
    then:  
      \- action: switch.turn\_on  
        target:  
          entity\_id: "{{ relays }}"  
  \- choose:  
      \- conditions:  
          \- alias: Target Scene Supplied  
            condition: template  
            value\_template: "{{ target\_scene \!= \-1 }}"  
        sequence:  
          \- variables:  
              posture\_offset\_map:  
                disarmed: 0  
                armed\_night: 5  
                armed\_away: 1  
              offset: "{{ posture\_offset\_map.get(current\_posture, 0\) | default(0) | int }}"  
              base\_id: "{{ target\_scene }}"  
          \- variables:  
              night\_shift\_id: "{{ target\_scene \+ offset }}"  
              night\_prefix: "{{ 'scene.' \~ target\_area \~ '\_' \~ night\_shift\_id | string \~ '\_' }}"  
              base\_prefix: "{{ 'scene.' \~ target\_area \~ '\_' \~ base\_id | string \~ '\_' }}"  
              base\_entity: \>-  
                {{ states.scene | selectattr('entity\_id', 'search', '^' \~ base\_prefix) | map(attribute='entity\_id') | first }}  
              night\_entity: \>-  
                {{ states.scene | selectattr('entity\_id', 'search', '^' \~ night\_prefix) | map(attribute='entity\_id') | first | default(base\_entity) }}  
              night\_name: \>-  
                {{ night\_entity | replace(base\_prefix if night\_entity \== base\_entity else night\_prefix, '', 1\) | replace('\_', ' ') | title }}  
              base\_name: \>  
                {{ base\_entity | replace(base\_prefix, '', 1\) | replace('\_', ' ') | title }}  
              scene\_id: "{{ base\_id if night\_entity \== '' else night\_shift\_id }}"  
              scene\_name: "{{ base\_name if night\_name \== '' else night\_name }}"  
              action: "{{ base\_id \~ ' ' \~ scene\_name }}"  
              target\_select: select.{{ target\_area }}\_matrix\_scene  
              current\_history: "{{ state\_attr(target\_select, 'history\_stack') | default(\[\], true) }}"  
              current\_scene: "{{ state\_attr(target\_select, 'scene') | default({}, true) }}"  
              local\_options: "{{ state\_attr(target\_select, 'options') | default(\[\], true) }}"  
              zb\_options: |-  
                {% set ns \= namespace(found=\[\]) %}  
                {%- set prefix \= 'scene.' \~ target\_area \~ '\_' %}  
                {%- for s in states.scene | selectattr('entity\_id', 'search', '^' \~ prefix \~ '\[0-9\]\*0\_') \-%}  
                  {%- set suffix \= s.entity\_id | replace(prefix, '', 1\) \-%}  
                  {%- set parts \= suffix.split('\_') \-%}  
                  {%- set found\_scene\_id \= parts\[0\] \-%}  
                  {%- set found\_scene\_name \= parts\[1:\] | join(' ') | title \-%}  
                  {%- set ns.found \= ns.found \+ \[ found\_scene\_id \~ ' ' \~ found\_scene\_name \] \-%}  
                {%- endfor \-%}  
                {{ ns.found | unique | sort }}  
              is\_zigbee\_scene: "{{ zb\_options is list and zb\_options | count \> 0 }}"  
              options: "{{ zb\_options if is\_zigbee\_scene else local\_options }}"  
              is\_option: "{{ action in options }}"  
          \- action: scene.turn\_on  
            target:  
              entity\_id: "{{ night\_entity }}"  
      \- conditions:  
          \- alias: Lights Turn Off No Target Scene  
            condition: template  
            value\_template: "{{ target\_scene \== \-1 and action\_type \== 'turn\_off' }}"  
        sequence:  
          \- alias: Hardware Bucketing and Target Expansion  
            variables:  
              area\_entities: "{{ area\_entities(target\_area) | select('match', 'light.\*') | list }}"  
              explicit\_entities: |-  
                {% set t \= payload.get('target', {}) %}   
                {{ t.get('entity\_id') | default(\[\], true) }}               
              intersected: |-  
                {% if target\_labels | count \> 0 %}  
                  {{ area\_entities | intersect(target\_labels) }}  
                {% else %}  
                  {{ area\_entities }}  
                {% endif %}  
              target\_entities: "{{ (intersected \+ explicit\_entities) | unique | list }}"  
              is\_whole\_area: "{{ val | count \== 0 }}"  
              lights\_off: |  
                {% if action\_type \== 'turn\_off' %}  
                  {{ target\_entities | expand | rejectattr('state', 'eq', 'off') | map(attribute='entity\_id') | list }}  
                {% else %}  
                  \[\]  
                {% endif %}  
              off\_target\_data: |  
                {% if is\_whole\_area %}  
                  {{ {"area\_id": target\_area} }}  
                {% else %}  
                  {{ {"entity\_id": lights\_off} }}  
                {% endif %}  
          \- alias: Standard Lights Turn Off  
            if:  
              \- condition: template  
                value\_template: "{{ lights\_off | count \> 0 or is\_whole\_area }}"  
            then:  
              \- action: light.turn\_off  
                target: "{{ off\_target\_data }}"  
              \- if:  
                  \- condition: template  
                    value\_template: "{{ is\_whole\_area }}"  
                then:  
                  \- event: area\_registry\_update  
                    event\_data:  
                      action\_type: lighting\_registry\_update  
                      action: purge  
                      domain: lighting  
                      claimant\_id: "{{ meta.get('claimant\_id', payload.source\_device) }}"  
                      intent\_type: "{{ meta.get('intent\_type', 'motion') }}"  
                      target:  
                        area\_id: "{{ target\_area }}"  
                      seconds: "{{ meta.get('seconds', 0\) | int }}"  
          \- action: logbook.log  
            data:  
              name: Light Engine (Off)  
              message: "Area: {{ target\_area }} | Off call completed"  
              entity\_id: "{{ log\_dest }}"  
      \- conditions:  
          \- alias: Lights Turn On No Target Scene  
            condition: template  
            value\_template: "{{ target\_scene \== \-1 and action\_type \== 'turn\_on'}}"  
        sequence:  
          \- alias: Data Constants  
            variables:  
              dim\_factor: 20  
              command\_map:  
                max: {brightness: 255}  
                raise: {brightness\_step: 35}  
                lower: {brightness\_step: \-35}  
                min: {brightness: 35}  
                night\_mode: {brightness: 35}  
                day\_mode: {brightness: 190}  
                release: {brightness\_step: 0}  
          \- alias: Hardware Bucketing and Target Expansion  
            variables:  
              area\_entities: "{{ area\_entities(target\_area) | select('match', 'light.\*') | list }}"  
              explicit\_entities: |-  
                {% set t \= payload.get('target', {}) %}   
                {{ t.get('entity\_id') | default(\[\], true) }}               
              intersected: |-  
                {% if target\_labels | count \> 0 %}  
                  {{ area\_entities | intersect(target\_labels) }}  
                {% else %}  
                  {{ area\_entities }}  
                {% endif %}  
              target\_entities: "{{ (intersected \+ explicit\_entities) | unique | list }}"  
              resolved\_targets: "{{ target\_entities if action\_type \== 'turn\_on' else \[\] }}"  
              target\_br: |-  
                {% set current\_cmd \= command\_map.get(action\_val, {}) %}   
                {% if 'brightness\_step' in current\_cmd %}  
                  {{ 255 if current\_cmd.brightness\_step \> 0 else \-1 }}  
                {% elif action\_val is number or (action\_val | is\_number) %}  
                  {{ (\[0, action\_val | int, 255\] | sort)\[1\] }}  
                {% else %}  
                  {{ current\_cmd.get('brightness', 190\) }}  
                {% endif %}  
              step\_val: "{{ command\_map.get(action\_val, {}).get('brightness\_step', 0\) }}"  
              ikea\_cct\_lights: |  
                {% set ns \= namespace(to\_update=\[\]) %}   
                {% for l in states.light | selectattr('entity\_id', 'in', resolved\_targets) if l.attributes.get('max\_color\_temp\_kelvin', 0\) | int \<= 4000 and 'color\_temp' in l.attributes.get('supported\_color\_modes', \[\]) %}  
                      {% set cur\_k \= l.attributes.get('color\_temp\_kelvin', 0\) | int(0) %}  
                      {% set cur\_br \= l.attributes.get('brightness', 0\) | int(0) %}  
                      {% set clamped\_k \= (\[l.attributes.get('min\_color\_temp\_kelvin', 2202\) | int, target\_kelvin, 4000\] | sort)\[1\] %}  
                      {% if (cur\_k \- clamped\_k) | abs \> 50 or (cur\_br \- target\_br) | abs \> 3 %}  
                        {% set ns.to\_update \= ns.to\_update \+ \[l.entity\_id\] %}  
                      {% endif %}  
                {% endfor %} {{ ns.to\_update }}  
              standard\_cct\_lights: \>  
                {% set ns \= namespace(to\_update=\[\]) %}   
                {% for l in states.light | selectattr('entity\_id', 'in', resolved\_targets) if l.entity\_id not in ikea\_cct\_lights and 'color\_temp' in l.attributes.get('supported\_color\_modes', \[\]) %}  
                  {% set cur\_k \= l.attributes.get('color\_temp\_kelvin', 0\) | int(0) %}  
                  {% set cur\_br \= l.attributes.get('brightness', 0\) | int(0) %}  
                  {% set min\_hw \= l.attributes.get('min\_color\_temp\_kelvin', 2200\) | int %}  
                  {% set max\_hw \= l.attributes.get('max\_color\_temp\_kelvin', 7000\) | int %}  
                  {% set clamped\_k \= (\[min\_hw, target\_kelvin, max\_hw\] | sort)\[1\] %}  
                  {% if (cur\_k \- clamped\_k) | abs \> 50 or (cur\_br \- target\_br) | abs \> 3 %}  
                    {% set ns.to\_update \= ns.to\_update \+ \[l.entity\_id\] %}  
                  {% endif %}  
                {% endfor %} {{ ns.to\_update }}  
              dimmer\_lights: "{{ resolved\_targets | intersect(label\_entities('CurrentCTDimmer')) | list }}"  
              binary\_lights: |  
                {{ resolved\_targets | expand | selectattr('attributes.supported\_color\_modes', 'defined') | selectattr('attributes.supported\_color\_modes', 'eq', \['onoff'\]) | selectattr('state', 'in', \['off'\]) | map(attribute='entity\_id') | list }}  
              excluded: "{{ ikea\_cct\_lights \+ standard\_cct\_lights \+ dimmer\_lights \+ binary\_lights | list | default(\[\]) }}"  
              standard\_lights: |  
                {{ resolved\_targets | reject('in', excluded) | expand | selectattr('state', 'in', \['off'\]) | map(attribute='entity\_id') | list }}  
              publish\_intent: "{{ (trigger.event.data.metadata.publish\_intent in \['add', 'remove', 'lock'\] or trigger.event.data.metadata.action in \['add', 'remove', 'lock'\]) and trigger.event.data.metadata is defined }}"  
          \- parallel:  
              \- alias: IKEA CCT Turn On  
                if:  
                  \- condition: template  
                    value\_template: "{{ ikea\_cct\_lights | length \> 0 }}"  
                then:  
                  \- action: light.turn\_on  
                    target:  
                      entity\_id: "{{ ikea\_cct\_lights }}"  
                    data: \>  
                      {% set base\_data \= {'color\_temp\_kelvin': target\_kelvin} %}  
                      {{ dict(base\_data, brightness\_step=step\_val) if step\_val \!= 0 else dict(base\_data, brightness=target\_br) if target\_br \!= \-1 else base\_data }}  
              \- alias: Standard CCT Turn On  
                if:  
                  \- condition: template  
                    value\_template: "{{ standard\_cct\_lights | length \> 0 }}"  
                then:  
                  \- action: light.turn\_on  
                    target:  
                      entity\_id: "{{ standard\_cct\_lights }}"  
                    data: \>  
                      {% set base\_data \= {'color\_temp\_kelvin': target\_kelvin} %}  
                      {{ dict(base\_data, brightness\_step=step\_val) if step\_val \!= 0 else dict(base\_data, brightness=target\_br) if target\_br \!= \-1 else base\_data }}  
              \- alias: Dimmer Lights Turn On  
                if:  
                  \- condition: template  
                    value\_template: "{{ dimmer\_lights | length \> 0 }}"  
                then:  
                  \- action: light.turn\_on  
                    target:  
                      entity\_id: "{{ dimmer\_lights }}"  
                    data:  
                      brightness: "{{ target\_br\_dimmer | int(150) }}"  
              \- alias: Binary Lights Turn On  
                if:  
                  \- condition: template  
                    value\_template: "{{ binary\_lights | length \> 0 }}"  
                then:  
                  \- action: light.turn\_on  
                    target:  
                      entity\_id: "{{ binary\_lights }}"  
              \- alias: Standard Lights Turn On  
                if:  
                  \- condition: template  
                    value\_template: "{{ standard\_lights | length \> 0 }}"  
                then:  
                  \- action: light.turn\_on  
                    target:  
                      entity\_id: "{{ standard\_lights }}"  
                    data: \>  
                      {% set base\_data \= {} %}  
                      {{ dict(base\_data, brightness\_step=step\_val) if step\_val \!= 0 else dict(base\_data, brightness=target\_br) if target\_br \!= \-1 else base\_data }}  
mode: queued  
max: 30

## **Production Automation YAML: UCC Loopback Coordinator V3.0**

alias: UCC \- Loopback Coordinator V3 (Native Scenes)  
description: \>-  
  Unified router for relative steering, posture-aware scene shifting, history tracking, and native scene execution.  
triggers:  
  \- trigger: event  
    id: bus\_event  
    event\_type: universal\_controller\_command  
    event\_data:  
      action\_type: scene\_cycle  
    enabled: true  
  \- trigger: event  
    event\_type: call\_service  
    event\_data:  
      domain: scene  
      service: turn\_on  
    id: core\_scene\_call  
  \- trigger: select.selection\_changed  
    target:  
      label\_id: scene  
    id: option\_change  
actions:  
  \- variables:  
      is\_service\_call: "{{ trigger.id \== 'core\_scene\_call' }}"  
      is\_option\_change: "{{ trigger.id \== 'option\_change' }}"  
      called\_scene\_entity: |-  
        {% if is\_service\_call %}  
          {{ trigger.event.data.service\_data.entity\_id\[0\] if trigger.event.data.service\_data.entity\_id is list else trigger.event.data.service\_data.entity\_id }}  
        {% else %}  
          none  
        {% endif %}  
      payload: |-  
        {% if is\_service\_call %}  
          {% set area \= area\_id(called\_scene\_entity) | default('none', true) %}  
          {% set parts \= called\_scene\_entity.split('.')\[1\].replace(area \~ '\_', '').split('\_') %}  
          {{ {'source\_device': 'native\_core\_scene\_call', 'target': {'area\_id': area}, 'action\_value': parts\[0\] \~ ' ' \~ (parts\[1:\] | join(' ') | title)} }}  
        {% elif is\_option\_change %}  
          {{ {'source\_device': 'native\_select\_option', 'target': {'area\_id': area\_id(trigger.to\_state.entity\_id)}, 'action\_value': trigger.to\_state.state} }}  
        {% else %}  
          {{ trigger.event.data }}  
        {% endif %}  
      target\_area: "{{ payload.get('target', {}).get('area\_id', 'none') }}"  
      action\_raw: "{{ payload.action\_value | default('next') | string }}"  
      target\_select: select.{{ target\_area }}\_matrix\_scene  
      current\_history: "{{ state\_attr(target\_select, 'history\_stack') | default(\[\], true) | replace(':','') }}"  
      options: \>-  
        {% set ns \= namespace(found=\[\]) %}  
        {% set prefix \= 'scene.' \~ target\_area \~ '\_' %}  
        {% for s in states.scene | selectattr('entity\_id', 'search', '^' \~ prefix \~ '\[0-9\]\*0\_') %}  
          {% set suffix \= s.entity\_id | replace(prefix, '', 1\) %}  
          {% set parts \= suffix.split('\_') %}  
          {% set ns.found \= ns.found \+ \[ parts\[0\] \~ ' ' \~ parts\[1:\] | join(' ') | title \] %}  
        {% endfor %}  
        {{ ns.found | unique | sort }}  
      t\_state: "{{ states(target\_select) }}"  
  \- variables:  
      action\_resolved: |-  
        {% if action\_raw in \['next', 'raise', 'select\_next'\] %}  
          {% set idx \= options.index(t\_state) | default(0, true) \+ 1 %}  
          {{ options\[idx\] if idx \< options | length else options\[idx\] }}  
        {% elif action\_raw in \['previous', 'lower', 'select\_previous'\] %}  
          {% set idx \= options.index(t\_state) | default(1, true) \- 1 %}  
          {{ options\[idx\] if idx \>= 0 else options\[-1\] }}  
        {% elif action\_raw in \['off', 'select\_first'\] %}  
          {{ options\[0\] if options | length \> 0 else '0 Off' }}  
        {% elif action\_raw in \['max', 'select\_last'\] %}  
          {{ options\[-1\] if options | length \> 0 else '0 Off' }}  
        {% elif action\_raw \== 'restore' %}  
          {% set active\_history \= current\_history | reject('match', '^0') | reject('eq', '0') | list %}  
          {{ active\_history\[-1\] if active\_history | length \> 0 else (options\[1\] if options | length \> 1 else options\[0\]) }}  
        {% elif action\_raw \== 'min' %}  
          {{ options\[1\] if options | length \> 1 else options\[0\] }}  
        {% else %}  
          {% set by\_id \= options | select('match', '^' \~ action\_raw.replace('5', '0') ) | first | default(none) %}  
          {% set by\_name \= options | select('search', action\_raw.replace('5', '0') ) | first | default(none) %}  
          {{ by\_id if by\_id is not none else (by\_name if by\_name is not none else action\_raw) }}  
        {% endif %}  
      is\_valid\_option: "{{ action\_resolved in options }}"  
      parts: "{{ action\_resolved.split(' ') if ' ' in action\_resolved else \[0, action\_resolved\] }}"  
      scene\_id: "{{ parts\[0\] | int(0) }}"  
      scene\_name: "{{ parts\[1:\] | join(' ') | default('Off') | title }}"  
      history\_update: "{{ (current\_history \+ \[action\_resolved\])\[-5:\] if action\_resolved \!= current\_history\[-1\] | default('') else current\_history }}"  
  \- condition: template  
    value\_template: "{{ is\_valid\_option and target\_area \!= 'none' }}"  
  \- variables:  
      current\_posture: \>-  
        {% set registry \= state\_attr('sensor.global\_variable\_registry', 'vars') | default({}, true) %}  
        {% set g\_logic \= registry.get('globals',{}).get('environmental',{}) %}  
        {{ states(g\_logic.get('home\_posture', '')) | default('disarmed', true) }}  
      posture\_offset\_map: {disarmed: 0, armed\_night: 5, armed\_away: 1}  
      offset: "{{ posture\_offset\_map.get(current\_posture, 0\) | default(0) | int }}"  
      base\_id: "{{ scene\_id }}"  
      night\_shift\_id: "{{ base\_id \+ offset }}"  
      night\_prefix: "{{ 'scene.' \~ target\_area \~ '\_' \~ night\_shift\_id \~ '\_' }}"  
      base\_prefix: "{{ 'scene.' \~ target\_area \~ '\_' \~ base\_id \~ '\_' }}"  
      base\_entity: "{{ states.scene | selectattr('entity\_id', 'search', '^' \~ base\_prefix) | map(attribute='entity\_id') | first | default(none) }}"  
      night\_entity: "{{ states.scene | selectattr('entity\_id', 'search', '^' \~ night\_prefix) | map(attribute='entity\_id') | first | default(base\_entity) }}"  
      matched\_scene: "{{ night\_entity if night\_entity is not none else base\_entity }}"  
  \- if:  
      \- condition: template  
        value\_template: "{{ not is\_service\_call }}"  
    then:  
      \- action: scene.turn\_on  
        target:  
          entity\_id: "{{ matched\_scene }}"  
  \- action: mqtt.publish  
    data:  
      topic: homeassistant/select/{{ target\_area }}/scene/attributes  
      retain: true  
      payload: \>-  
        {{ {'options': options, 'scene': {'scene\_id': base\_id, 'scene\_name': scene\_name}, 'friendly\_name': state\_attr(target\_select, 'friendly\_name'), 'icon': state\_attr(target\_select, 'icon'), 'history\_stack': history\_update} | tojson }}  
  \- action: mqtt.publish  
    data:  
      topic: homeassistant/select/{{ target\_area }}/scene/state  
      retain: true  
      payload: "{{ {'scene\_id': base\_id, 'scene\_name': scene\_name} | tojson }}"  
  \- action: logbook.log  
    data:  
      name: UCC Loopback V3  
      message: "Resolved command '{{ action\_raw }}' \-\> Activated native scene '{{ matched\_scene }}' for area \[{{ area\_name(target\_area) }}\]"  
      entity\_id: "{{ target\_select }}"  
mode: parallel  
max: 20  


[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAKQAAAAUCAYAAAADf5Y0AAAEdklEQVR4Xu1ZTWiTQRCtBEFRQYVasWk2tdWA4MUiioIHK4oU1INKEXr0IIgKFvSsB8GD4MmDVMSLIP4gFKQUqiKIggcPXkTtQapIxUItBaUFfS+ZSadj2uSr6U+a78Gys7Oz++1O3uxfampixIgRI0aMGDFixCgT0un0kRDCTU2pVOqG1kn5OPLLtk21oNJ8g7Hc8bqKBSbzp76+Pul0w7ZcraBvCugWnG9mm5D0g0mDru4bsiVMkMdtXWQ0NDQ0eaej/KAm94GqRiX5Zg4I+Q7pJnaOw05/wvoIO0cHygetTSSgcS9SN+VkMrkcHzznbaoVleSbYoTk2GFzy+tLBdr2eR0B/QjSRy0jiDeg/MPaRALZze0azD5rmR5jwjfIfy503xQjpEFC5pLwFdMBbQaRToMnuy3h2FcBQs7MV7ol4SOvEUE7KGMl2OrtFigSGOsmrywXrG+4OhbzDexavW424ecegZBZYLw9aDPg9VMBts+MzFXxrcjlIyQa9tnGkC+F/z2UzhHg0M8Iooter8A8Pk2XvL1HFN9gLFdQ98HrZwsMFj/3EJGQCiHQaEtLy1JfNxWsb5iHMhJyHGnEqHhL4gd2Gd2CBMfpXwbKiSi+KRYc5QYDwM89zJCQaDeGdNXrLThnS7IwmZBDwRASY9uC8nctRwI7hSNPeZ39uAIfOiPb+jax6WxqalrnBvpe8i7YH0X+m5EX5MwhW984+mlHPqY3NuqQGkVuk2jNEgD93Bb9pINymEyWsoPfLtU31NkVBuVOzHWt1qmeWz7m8xy6LqQvwZBI7egbEpxybW3tSh4ZKNsjAWx/q2x0JRMSfe2D/cdSV0XYbwQ2a5m+5/hFPmjnyMBsbGzcr+WSgA7OsxNN+OBJ0dNRPMBzW7NEuxdyb00ED8MJfHinkC17++IgdCCsg/49I1n7aG5urq2rq1sB/X3VESi/5BaEtnVBziVon6a9G0NeLrRllQshom+kzm7XDKR8sKit/vi+reiecE6UkW/HNzswv9Vim4BvMsG8/U3RR1FCwmYA6aHXlwKM5zHa9iONYXxnbV3ILVLsm+mFrZsV0AGWXAquIHSg2HSjvEzr2EadrBDS7rE62hWKVPaNuq+U5aab/xE4Fr9lzRd8cGCcbbqqE7raET7IFG5ut5HWpHI7zD+2RChwXg1FCIn6Ua+rWAi5ssQjIB8Sff7sYJyXfTQOBS4A9sdRwO6XLePHPSD6EchHKLNdyF0qnkhdtu9MJrNqouX8AGPp1UBEvp5EUl9BbhVivRHb+6HAe571ncoMXshDxkz92sY6zh19n9HKUISQiwqY+IUg137kr1DeRxk/wPV0bmt5RUdCbpcmdOx0js8DfR3TJwzIPaqnrRIO8jDPMByHlBntfE/rV/v5AsbwSPKnouLc+V83z2nP4JMdZhcZ0iCz4LxSucsAz2b2mKKrGueafaJBvleepCbNPVQTIWPMDUCquyDmc68vBWh7zetixIiMkHt1uM4bdZCba4wY8wo+B+FcGLx+seIvx0iMVfgxGxEAAAAASUVORK5CYII=>

[image2]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAALIAAAAUCAYAAAApz2ebAAAFV0lEQVR4Xu1ZUYiVRRT+lyXYoEKLBXV379y1hUUpQpYSDGV9SSPIHlTyIRLpJQiK9sGIoKfoIQhkwQJZEVF8UAjB6iGShIgCH1x8aVm1EJXYUNAluqCg3/f/51zPPXfu7V+52/56/w8OM/PN+efOnDkzc2ZukpQoUaJEiRIlSpQoUSIXqtXqeAjhQETe87pERG9ycHBwxOt1GyJ2oXwB+y7zupVK5SuvC70tXq8IQN8Oe67QQIfvwsDLtcwJIGd1FORR/66WBwYGBsmNjY09ZvW6DbDBJdjwLcfVYKt9liOoh7prlkP5JvgdlltqLKYji4/9xTzH3crfcgMNrog1EuMI8iMjI/2es87djRC7POW405ALliMwcWfAT1pOdBuce6mxmI6MtqesjzE/PDz8itVZENDACW9UWSF3LEfwh8DfsBzKG9iJbt6RYZdNdlIIPdV4YlmeIB9xep6K2y231GjnyP39/U+gfg59Xu3r8gLfb2bKaIDjj4ViuSENvI3GdkL20oEhe7weAX7W7Ly9KF/gYBqUuhCwwbQ4Im3IsOEs0kOo6vG6sN8b1NUy7hjPszw0NLTR6hUB7RzZAnrnOWbP5wE2gVGx3fu+LjcYIlijEigfpTNbTkFdyB5OGNJJyFWvU0TAWR73XCchE3HGUFzkdM7XDZciZCGEOj3tyI1jZURvXRJZCIuIXk+EnI4s6JGxvOMr2gE2WoVvfg8PuBBShCysaIqFwdUgn0R47/R3IactVzTAWT6PHe8K9P9iO0lyOBPtgN9Z67hT3l7CNzg9Q4xWekmO3+4U0KfLngsLc+Q68N1+tPep59sB3/wN+d7zuYAP59lAhG+6vKHc5w3OMifMckVDbII6Cd4NvF2IkB23Mb4hFpZ7R0zvuucWEy36sGBHxthWB3ePigE6RyA/mTLD1KY+5IIY1T8Z/RNrkDsb+GnLUQ8O/pHkv5P0OuNAeZabkt2Qx07apj7Xie6M7Eg1Hv/kcdS8qHEjvw8mfEH+tslPMIX+c6J7SXj2qc/oNY2lk+D4YZvfLIf+Py39WG/5ilxqLBeyCUydFumXTDl+Ny+0Xzp22iNI6EdbefvpB8gfh0xJnnZ9VvJ3JNRimzPk0M8tyM/rt4qQ35EZSv2Kdnb5ilZgn1x/GQWk/c0N/OA2bcjJFf/6AMd7xun8onXI34bcgvybZIb5DPKqVKfHIn5rXG71qfFDduSmu7hM+IQaWfWZ+p0UesfYDuqryP8Iqkf7anXZR9aZ8qzmO4nR0dEnxR5ebqE/e71+kA1CRfmqvG5ADmJ8L5GThWHHwKepTZKf4aYi344HZz+CjhqxCdObtJnEpXMaclG3KhuSRfgPR5bFwwX2ICEQ/WUO8qeM/2evsGRAZ2p+IQg/Xclu8akOj1NbV1cU8BKqk6WA3g0++ViOkAtr/fkwmLdYTnBsgooOTmyknDoL89ZxY/YDN0GRYo+eGLYdC/Kxe0Ro48io+wOy3/OPBDCwmi3DiXYLT+Ov0jxTHott4ssT3PEc1/BngWm7rkvnr2QxWnoqIP0Ben3gtiNdYT4vLNDndWqTcD80qMfLWqd/SrWwH3dptffHbFPyfoF8KGk6b8Fd3EMbR36kAYfZgd32BebhOCeT+7vIVZTfhHxAY/I4FZ31IfLUFyKXBeqi/ZeTbIc5xJS81UX+GHmk56T8DVPof606RQf6vAYyj/Fu5QIULv3DCeksx8t7gdFvsl+S2eDb4eyN1t4rDuhTZMhi8/TZT8KQXg1tjH53OnKJ4oGLwHN5EeTyWaLE/w4432vqvNjV9yG/weuUKPFQgHcGOPG22MX7YcY9LhbNf0oov5YAAAAASUVORK5CYII=>