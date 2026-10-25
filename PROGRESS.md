# OverSight HA Integration — Progress

## Pre-Phase: Android App GET /info Endpoint ✅
- Added `GET /info` route returning full `InfoValues` + `deviceId`
- Built and deployed to Shield TV

## Phase 1: Foundation ✅
- Rewrote `const.py`, `api.py`, `coordinator.py`, `data.py`, `config_flow.py`, `entity.py`, `__init__.py`
- Manual host/port config flow with device validation
- `OversightDeviceState` dataclass with 30s polling
- Connectivity binary sensor
- Deleted placeholder `sensor.py`
- Updated `manifest.json` to v0.1.0

## Phase 2: Config Entities ✅
- Number entities: overlay visibility, clock visibility, notification duration
- Select entity: hot corner position
- Switch entities: display notifications, display fixed notifications, pixel shift
- All entities have `entity_category: CONFIG`

## Phase 3: Zeroconf Discovery ✅
- Added `_tvoverlay._tcp.local.` to manifest.json zeroconf
- Zeroconf config flow: auto-discovers devices, shows confirmation
- Auto-updates IP when device moves (via `_abort_if_unique_id_configured(updates=...)`)

## Phase 4: Notify Platform & Services ✅
- `NotifyEntity` for popup notifications with optional fields (source, image, video, icons, corner, duration)
- Custom services: `send_fixed_notification`, `remove_fixed_notification`, `screen_on`
- Services resolve target device via entity targeting (multi-device safe)
- `services.yaml` with full field definitions

## Phase 5: Review Fixes & API Coverage ✅
- Actions are platform entity services registered in `async_setup`; device and area targets reach every matched device
- New entities: notification layout select, display debug switch (disabled by default), device name text, screen on and restart buttons
- New action `set_clock_appearance` (merges onto the current clock settings); `send_notification` gains `id` and `layout`
- `remove_fixed_notification` hides the badge and expires it after 1s so the device deletes it
- Setting changes apply the state the device returns instead of waiting for the next poll
- Diagnostics, icons, `PARALLEL_UPDATES`, translated selector options; translations are the single source of action text
- Test suite (pytest-homeassistant-custom-component) with a CI workflow

## Phase 6: App Status & Badge Delete ✅
- Uses the app's new status report: Screen sensor, Overlay permission and Battery optimization problem sensors, app version on the device page (kept current on app updates)
- `remove_fixed_notification` uses `DELETE /notify_fixed/{id}` (404 counts as already gone)
- Older apps without status keep working: status sensors are unavailable and badge removal falls back to hide + 1s expiration
