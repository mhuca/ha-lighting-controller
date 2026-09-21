# python_scripts/fire_ucc_event.py
event_type = data.get("event_type", "universal_controller_command")
raw_data = data.get("event_data", {})

payload = None

# 1. Test if raw_data is already a mapping/dictionary
try:
    _ = raw_data.keys()
    payload = raw_data
except Exception:
    pass

# 2. If not a dictionary, attempt JSON string parsing
if payload is None:
    try:
        parsed = json.loads(raw_data)
        try:
            _ = parsed.keys()
            payload = parsed
        except Exception:
            payload = {"payload": parsed}
    except Exception:
        payload = {"payload": raw_data}

# 3. Fire safely onto event bus
try:
    _ = payload.keys()
    hass.bus.fire(event_type, payload)
except Exception as err:
    logger.error("Could not fire event %s: payload is not a valid dictionary (%s)", event_type, err)

# # python_scripts/fire_ucc_event.py
# event_type = data.get("event_type", "universal_controller_command")
# raw_data = data.get("event_data", {})

# payload = None

# # 1. Direct dictionary pass
# if isinstance(raw_data, dict):
#     payload = raw_data

# # 2. String processing (JSON attempt vs plain string)
# elif isinstance(raw_data, str):
#     try:
#         parsed = json.loads(raw_data)
#         if isinstance(parsed, dict):
#             payload = parsed
#         else:
#             payload = {"payload": parsed}
#     except Exception:
#         payload = {"payload": raw_data}

# # 3. Fallback for any other data type (int, list, bool)
# else:
#     payload = {"payload": raw_data}

# # 4. Safely fire onto event bus (Guaranteed dict structure)
# hass.bus.fire(event_type, payload)

# # python_scripts/fire_ucc_event.py
# event_type = data.get("event_type", "universal_controller_command")
# raw_data = data.get("event_data", {})

# payload = None

# # 1. Attempt parsing as string JSON payload
# try:
#     payload = json.loads(raw_data)
# except Exception:
#     pass

# # 2. If parsing failed, assume it was already a dict/mapping object
# if payload is None:
#     payload = raw_data

# # 3. Fire onto event bus if valid mapping object exists
# try:
#     _ = payload.get
#     hass.bus.fire(event_type, payload)
# except Exception as err:
#     logger.error("Could not fire event %s: payload is not a mapping (%s)", event_type, err)