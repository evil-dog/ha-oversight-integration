# OverSight HA Integration — Developer Tools Test YAML

Paste each block into **Developer Tools → Actions** (YAML mode). Replace `notify.oversight_android_tv` with your entity's actual entity_id (check Settings → Devices & Services → OverSight → entities).

> **Color values must be quoted** in YAML — `#` starts a comment. Always write `"#FF5733"` with quotes, never bare `#FF5733`.

---

## Connectivity / State

### Read device state (via coordinator — check entity states in Dev Tools → States)
No action needed. Entities update automatically every 30 seconds. Force a refresh:
```yaml
action: homeassistant.update_entity
target:
  entity_id: notify.oversight_android_tv
```

---

## Overlay Settings

### Set background dimmer to 30%
```yaml
action: number.set_value
target:
  entity_id: number.oversight_android_tv_overlay_visibility
data:
  value: 30
```

### Set clock opacity to 80%
```yaml
action: number.set_value
target:
  entity_id: number.oversight_android_tv_clock_overlay_visibility
data:
  value: 80
```

### Set hot corner to bottom-right
```yaml
action: select.select_option
target:
  entity_id: select.oversight_android_tv_hot_corner
data:
  option: bottom_end
```

### Restore hot corner to top-right
```yaml
action: select.select_option
target:
  entity_id: select.oversight_android_tv_hot_corner
data:
  option: top_end
```

---

## Notification Settings

### Disable popup notifications
```yaml
action: switch.turn_off
target:
  entity_id: switch.oversight_android_tv_display_notifications
```

### Re-enable popup notifications
```yaml
action: switch.turn_on
target:
  entity_id: switch.oversight_android_tv_display_notifications
```

### Set notification duration to 5 seconds
```yaml
action: number.set_value
target:
  entity_id: number.oversight_android_tv_notification_duration
data:
  value: 5
```

### Restore notification duration to 8 seconds
```yaml
action: number.set_value
target:
  entity_id: number.oversight_android_tv_notification_duration
data:
  value: 8
```

### Disable fixed notifications
```yaml
action: switch.turn_off
target:
  entity_id: switch.oversight_android_tv_display_fixed_notifications
```

### Re-enable fixed notifications
```yaml
action: switch.turn_on
target:
  entity_id: switch.oversight_android_tv_display_fixed_notifications
```

### Set fixed notifications visibility to 50% (semi-transparent)
```yaml
action: number.set_value
target:
  entity_id: number.oversight_android_tv_fixed_notifications_visibility
data:
  value: 50
```

### Restore fixed notifications visibility to 100%
```yaml
action: number.set_value
target:
  entity_id: number.oversight_android_tv_fixed_notifications_visibility
data:
  value: 100
```

### Toggle pixel shift
```yaml
action: switch.turn_on
target:
  entity_id: switch.oversight_android_tv_pixel_shift
```
```yaml
action: switch.turn_off
target:
  entity_id: switch.oversight_android_tv_pixel_shift
```

### Switch notification layout
Options come from the device, including custom layouts.
```yaml
action: select.select_option
target:
  entity_id: select.oversight_android_tv_notification_layout
data:
  option: Minimalist
```

### Rename the device
The new name is also advertised over mDNS.
```yaml
action: text.set_value
target:
  entity_id: text.oversight_android_tv_device_name
data:
  value: Living Room TV
```

### Show debug info
The switch is disabled by default; enable it under the device's entities first.
```yaml
action: switch.turn_on
target:
  entity_id: switch.oversight_android_tv_display_debug_info
```

---

## Popup Notifications — Custom Service

### Minimal notification (message only)
```yaml
action: oversight_android_tv_notifications.send_notification
target:
  entity_id: notify.oversight_android_tv
data:
  message: Hello from Home Assistant
```

### Full notification with all fields
```yaml
action: oversight_android_tv_notifications.send_notification
target:
  entity_id: notify.oversight_android_tv
data:
  message: Front door motion detected
  title: Security Alert
  source: Home Assistant
  large_icon: mdi:home-alert
  small_icon: mdi:bell
  small_icon_color: "#FF5733"
  corner: top_end
  duration: 10
```

### Notification with image
```yaml
action: oversight_android_tv_notifications.send_notification
target:
  entity_id: notify.oversight_android_tv
data:
  message: Snapshot attached
  title: Camera
  large_icon: mdi:camera
  image: https://dummyimage.com/400x200/333333/ffffff.png&text=Camera+Snapshot
  duration: 12
```

### Notification at bottom-left corner
```yaml
action: oversight_android_tv_notifications.send_notification
target:
  entity_id: notify.oversight_android_tv
data:
  message: Playing now
  title: Media
  large_icon: mdi:play-circle
  corner: bottom_start
  duration: 6
```

---

## Popup Notifications — Replace in Place

### Update the popup on screen instead of queueing another
Send twice with the same `id` and `source`; the second replaces the first while it is showing.
```yaml
action: oversight_android_tv_notifications.send_notification
target:
  entity_id: notify.oversight_android_tv
data:
  id: washer
  source: Laundry
  title: Washer
  message: 10 minutes left
```

---

## Popup Notifications — Notify Entity

### Via notify entity (message and title only)
```yaml
action: notify.send_message
target:
  entity_id: notify.oversight_android_tv
data:
  message: Hello via notify entity
  title: Test
```

`notify.send_message` only takes a message and title. Use `oversight_android_tv_notifications.send_notification` for icons, image, video, corner and duration.

---

## Fixed Notification Badges

### Create a basic badge (icon only)
```yaml
action: oversight_android_tv_notifications.send_fixed_notification
target:
  entity_id: notify.oversight_android_tv
data:
  id: test-basic
  icon: mdi:bell
```

### Create a badge with text and colors
> Note: hex colors **must be quoted** in YAML — `"#FF5733"` not `#FF5733`
```yaml
action: oversight_android_tv_notifications.send_fixed_notification
target:
  entity_id: notify.oversight_android_tv
data:
  id: test-colors
  icon: mdi:alert-circle
  text: Warning
  icon_color: "#FF5733"
  message_color: "#FFFFFF"
  background_color: "#CC880000"
  border_color: "#FF0000"
```

### Badge with shape and size
```yaml
action: oversight_android_tv_notifications.send_fixed_notification
target:
  entity_id: notify.oversight_android_tv
data:
  id: test-shape
  icon: mdi:weather-sunny
  text: 22°C
  shape: rounded
  size: big
  icon_color: "#FFC107"
```

All valid shape values: `circle`, `rounded`, `rectangular`
All valid size values: `small`, `normal`, `big`

### Badge that expires in 30 minutes
```yaml
action: oversight_android_tv_notifications.send_fixed_notification
target:
  entity_id: notify.oversight_android_tv
data:
  id: test-expiry
  icon: mdi:timer
  text: 30m timer
  expiration: 30m
```

Other expiration formats: `30s`, `2h`, `1d12h` (units `y w d h m s`), a number of seconds such as `600`, or a Unix timestamp in seconds or milliseconds

### Badge with collapsible animation (shows text for 5s, collapses, re-expands every 15s)
```yaml
action: oversight_android_tv_notifications.send_fixed_notification
target:
  entity_id: notify.oversight_android_tv
data:
  id: test-collapse
  icon: mdi:motion-sensor
  text: Motion
  icon_color: "#FF9800"
  show_duration: 5
  collapse_duration: 15
  repeat_expand: true
```

### Update an existing badge (partial update — only fields you include change)
```yaml
action: oversight_android_tv_notifications.send_fixed_notification
target:
  entity_id: notify.oversight_android_tv
data:
  id: test-colors
  text: Updated text
  icon_color: "#4CAF50"
```

### Hide a badge (set visible: false via update)
```yaml
action: oversight_android_tv_notifications.send_fixed_notification
target:
  entity_id: notify.oversight_android_tv
data:
  id: test-basic
  visible: false
```

### Remove a badge permanently
```yaml
action: oversight_android_tv_notifications.remove_fixed_notification
target:
  entity_id: notify.oversight_android_tv
data:
  id: test-colors
```

### Remove multiple badges (call once per badge)
```yaml
action: oversight_android_tv_notifications.remove_fixed_notification
target:
  entity_id: notify.oversight_android_tv
data:
  id: test-shape
```
```yaml
action: oversight_android_tv_notifications.remove_fixed_notification
target:
  entity_id: notify.oversight_android_tv
data:
  id: test-collapse
```
```yaml
action: oversight_android_tv_notifications.remove_fixed_notification
target:
  entity_id: notify.oversight_android_tv
data:
  id: test-expiry
```

---

## Device Control

### Wake screen
```yaml
action: oversight_android_tv_notifications.screen_on
target:
  entity_id: notify.oversight_android_tv
```
Or press `button.oversight_android_tv_screen_on`.

### Restart the overlay service
The device drops off for a moment while it restarts.
```yaml
action: button.press
target:
  entity_id: button.oversight_android_tv_restart_overlay_service
```

### Target several devices at once
Actions accept device and area targets and run on every OverSight device they cover.
```yaml
action: oversight_android_tv_notifications.send_notification
target:
  area_id: living_room
data:
  message: Dinner is ready
```

---

## Clock Appearance

### Make the clock bigger and bold (other settings are kept)
```yaml
action: oversight_android_tv_notifications.set_clock_appearance
target:
  entity_id: notify.oversight_android_tv
data:
  font_size: 20
  font_weight: bold
```

### Clock colors
```yaml
action: oversight_android_tv_notifications.set_clock_appearance
target:
  entity_id: notify.oversight_android_tv
data:
  color: "#FFD700"
  background_color: "#80000000"
  display_shadow: false
```

---

## Automation Examples

### Notify on motion with camera snapshot
```yaml
automation:
  trigger:
    - platform: state
      entity_id: binary_sensor.front_door_motion
      to: "on"
  action:
    - action: oversight_android_tv_notifications.send_notification
      target:
        entity_id: notify.oversight_android_tv
      data:
        title: Motion Detected
        message: Front door camera triggered
        large_icon: mdi:motion-sensor
        small_icon: mdi:cctv
        small_icon_color: "#FF5733"
        duration: 10
```

### Persistent badge while alarm is armed
```yaml
automation:
  - alias: Show alarm badge when armed
    trigger:
      - platform: state
        entity_id: alarm_control_panel.home
        to: armed_away
    action:
      - action: oversight_android_tv_notifications.send_fixed_notification
        target:
          entity_id: notify.oversight_android_tv
        data:
          id: alarm-status
          icon: mdi:shield-lock
          text: Armed Away
          icon_color: "#F44336"
          background_color: "#CC330000"
          shape: rounded

  - alias: Remove alarm badge when disarmed
    trigger:
      - platform: state
        entity_id: alarm_control_panel.home
        to: disarmed
    action:
      - action: oversight_android_tv_notifications.remove_fixed_notification
        target:
          entity_id: notify.oversight_android_tv
        data:
          id: alarm-status
```
