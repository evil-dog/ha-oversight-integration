# OverSight Android TV Notifications

Show Home Assistant notifications on your Android TV and control the OverSight overlay from Home Assistant.

[OverSight](https://github.com/evil-dog/oversight) is an Android TV app that draws an overlay on top of whatever is playing: popup notifications, fixed badges (small persistent indicators such as weather or alarm state), a clock and a background dimmer. This integration talks to the app's local REST API, so no cloud account is needed.

**Use it to:** show a camera snapshot when someone rings the doorbell, keep an "alarm armed" badge on screen, put the washer's countdown in the corner, or dim the overlay at night.

## Supported devices

Any Android TV device running the OverSight app on the same network as Home Assistant. Each device is added separately.

## Installation

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=evil-dog&repository=ha-oversight-integration&category=integration)

<details>
    <summary>Click to show installation instructions</summary>
    <ol>
        <li>Install files:</li>
        <ul>
            <li>
                <u>Using HACS:</u><br />
                In the HACS panel, go to integrations and click the big orange '+' button.
                Search for 'OverSight Android TV Notifications' and click 'Install this repository in HACS'.
            </li>
            <li>
                <u>Manually:</u><br />
                Download the <a href="https://github.com/evil-dog/ha-oversight-integration/releases">latest release</a> as a zip file and extract it into the `custom_components` folder in your HA installation.
            </li>
        </ul>
        <li>Restart HA to load the integration into HA.</li>
        <li>Devices running OverSight are discovered automatically and appear under Settings → Devices &amp; services. To add one by hand, click 'Add integration', search for OverSight Android TV Notifications, and enter:
            <ul>
                <li><b>Host</b>: the IP address or hostname of the Android TV device.</li>
                <li><b>Port</b>: the OverSight API port, shown in the app's settings (default <code>5001</code>).</li>
            </ul>
        </li>
    </ol>
</details>

The integration has no other options. If a device's IP address changes, discovery updates it automatically.

## Updating

<details>
    <summary>Click to show updating instructions</summary>
    <ol>
        <li>Update the files:
            <ul>
                <li>
                    <u>Using HACS:</u><br>
                    In the HACS panel, there should be a notification when a new version is available. Follow the instructions within HACS to update the installation files.
                </li>
                <li>
                    <u>Manually:</u><br>
                    Download the <a href="https://github.com/evil-dog/ha-oversight-integration/releases">latest release</a> as a zip file and extract it into the <code>custom_components</code> folder in your HA installation, overwriting the previous installation.
                </li>
            </ul>
        </li>
        <li>Restart HA to load the changes.</li>
    </ol>
</details>

## Uninstalling

<details>
    <summary>Click to show uninstall instructions</summary>
    <ol>
        <li>
            <u>Remove OverSight Android TV Notifications from HA:</u><br>
            In HA go to Settings → Devices &amp; services. In the OverSight Android TV Notifications card, click the button with the 3 dots, and click 'Delete'.
        </li>
        <li>Remove the files:
            <ul>
                <li>
                    <u>When installed with HACS:</u><br />
                    In the HACS panel go to integrations and look for OverSight Android TV Notifications.
                    Click the button with the 3 dots and click 'Uninstall'.
                </li>
                <li>
                    <u>When installed manually:</u><br />
                    In the <code>custom_components</code> directory, remove the 'oversight_android_tv_notifications' folder.
                </li>
            </ul>
        </li>
        <li>Restart HA to make all traces of the component disappear.</li>
    </ol>
</details>

## Entities

Each device gets these entities:

| Entity | Type | What it does |
|---|---|---|
| Connectivity | Binary sensor | On while the device answers; off when it can't be reached |
| Notifications | Notify | Sends a popup with `notify.send_message` (message and title) |
| Overlay visibility | Number | Background dimmer opacity, 0–95% |
| Clock overlay visibility | Number | Clock opacity, 0–100% |
| Notification duration | Number | Default popup display time, 3–30 s |
| Fixed notifications visibility | Number | Badge opacity, 0–100% |
| Hot corner | Select | Corner where popups and badges appear |
| Notification layout | Select | Popup layout; lists the device's built-in and custom layouts |
| Display notifications | Switch | Show or suppress popups |
| Display fixed notifications | Switch | Show or hide badges |
| Pixel shift | Switch | Move the overlay slightly every minute to prevent burn-in |
| Display debug info | Switch | Show the app's debug overlay (disabled by default) |
| Device name | Text | Name the device advertises on the network |
| Screen on | Button | Wake the screen |
| Restart overlay service | Button | Restart the OverSight service on the device |

## Actions

Actions target the device's notify entity. You can also target devices or areas, and the action runs on every OverSight device they include.

| Action | What it does |
|---|---|
| `oversight_android_tv_notifications.send_notification` | Popup with optional title, source, icons, image, video, corner, duration and per-popup layout. Reusing an `id` replaces the popup on screen. |
| `oversight_android_tv_notifications.send_fixed_notification` | Create or update a badge. On updates, fields you leave out keep their values. |
| `oversight_android_tv_notifications.remove_fixed_notification` | Remove a badge. |
| `oversight_android_tv_notifications.screen_on` | Wake the screen. |
| `oversight_android_tv_notifications.set_clock_appearance` | Change the clock's font size, weight, colors and shadow. Fields you leave out keep their values. |

Each field is described in Developer tools → Actions.

### Examples

Camera snapshot when the doorbell rings:

```yaml
automation:
  - alias: Doorbell on TV
    triggers:
      - trigger: state
        entity_id: binary_sensor.doorbell
        to: "on"
    actions:
      - action: oversight_android_tv_notifications.send_notification
        target:
          entity_id: notify.living_room_tv_notifications
        data:
          title: Doorbell
          message: Someone is at the front door
          source: Home Assistant
          large_icon: mdi:doorbell
          image: http://homeassistant.local:8123/api/camera_proxy/camera.front_door
          duration: 15
```

Badge while the alarm is armed, removed when disarmed:

```yaml
action: oversight_android_tv_notifications.send_fixed_notification
target:
  entity_id: notify.living_room_tv_notifications
data:
  id: alarm
  icon: mdi:shield-lock
  text: Armed
  icon_color: "#FF5252"
```

```yaml
action: oversight_android_tv_notifications.remove_fixed_notification
target:
  entity_id: notify.living_room_tv_notifications
data:
  id: alarm
```

Quote color values in YAML: `#` starts a comment, so write `"#FF5252"`, not `#FF5252`. [TESTING.md](TESTING.md) has an example for every entity and action.

## How data is updated

The integration polls each device every 30 seconds. When you change a setting from Home Assistant, the new state shows up right away; changes made on the TV itself appear at the next poll.

## Known limitations

- Badges can't be listed or read back from Home Assistant; badges only flow from Home Assistant to the device.
- Removing a badge hides it immediately and the device deletes it about a second later, because the app's API has no delete call.
- The device doesn't report its screen state or app version yet, so there are no entities for them.
- Brand images (logo and icon) are not included yet.

## Troubleshooting

- **The device isn't discovered:** make sure Home Assistant and the TV are on the same network and that mDNS (multicast) isn't blocked, or add the device by hand with its IP address and port.
- **"Unable to connect":** check that the OverSight app is running and that the port matches the one in the app's settings.
- **"The device did not report a device ID":** the app is still starting; wait a moment and try again.
- **An action fails with a message from the device** (for example "Invalid MDI icon name"): the device rejected a field value. The message names the field.
- **Connectivity is off:** the device is asleep, off the network, or the app's service stopped. Press *Restart overlay service* once the device is reachable again.

## Issues

Before posting a new issue:

1. Check warnings and errors on the [Logs page](https://my.home-assistant.io/redirect/logs/)
2. Turn on debug logging: Settings → Devices &amp; services → **OverSight Android TV Notifications** → 3 dots → Enable debug logging. Reproduce the problem, then turn it off again to download the log.
3. Check **open and closed** [issues](https://github.com/evil-dog/ha-oversight-integration/issues?q=is%3Aissue)
4. Share the integration's [diagnostics](https://www.home-assistant.io/integrations/diagnostics/):

- All devices: Settings → [Devices & services](https://my.home-assistant.io/redirect/integrations/) → **OverSight Android TV Notifications** → 3 dots → Download diagnostics
- One device: Settings → [Devices](https://my.home-assistant.io/redirect/devices/) → Device → Download diagnostics

*Diagnostics leave out the device's IP address. There is no other private data, but you can delete anything you think is private.*
