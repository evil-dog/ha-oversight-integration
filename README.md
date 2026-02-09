# Oversight Android TV Notifications

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
                Search for 'Oversight Android TV Notifications' and click 'Install this repository in HACS'.
            </li>
            <li>
                <u>Manually:</u><br />
                Download the <a href="https://github.com/evil-dog/ha-oversight-integration/releases">latest release</a> as a zip file and extract it into the `custom_components` folder in your HA installation.
            </li>
        </ul>
        <li>Restart HA to load the integration into HA.</li>
        <li>Go to Configuration -> Integrations and click the big orange '+' button. Look for Oversight Android TV Notifications and click to add it.</li>
    </ol>
</details>

## Updating

<details>
    <summary>Click to show updating instructions</summary>
    <ol>
        <li>Update the files:
            <ul>
                <li>
                    <u>Using HACS:</u><br>
                    In the HACS panel, there should be an notification when a new version is available. Follow the instructions within HACS to update the installation files.
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
            <u>Remove Oversight Android TV Notifications from HA:</u><br>
            In HA go to Configuration -> Integrations. In the Oversight Android TV Notifications card, click the button with the 3 dots, and click 'Delete'.
        </li>
        <li>Remove the files:
            <ul>
                <li>
                    <u>When installed with HACS:</u><br />
                    In the HACS panel go to integrations and look for Oversight Android TV Notifications.
                    Click the button with the 3 dots and click 'Uninstall'.
                </li>
                <li>
                    <u>When installed manually:</u><br />
                    In the <code>custom_components</code> directory, remove the 'oversight_android_tv_notifications' folder.
                </li>
            </ul>
        </li>
        <li>Restart HA to make all traces of the component dissapear.</li>
    </ol>
</details>

## Issues

Before posting new issue:

1. Check the number of online devices on the [System Health page](https://my.home-assistant.io/redirect/system_health)
2. Check warning and errors on the [Logs page](https://my.home-assistant.io/redirect/logs/)
3. Check **debug logs** on the [Debug page](#debug-page) (must be enabled in integration options)
4. Check **open and closed** [issues](https://github.com/evil-dog/ha-oversight-integration/issues?q=is%3Aissue)
5. Share integration [diagnostics](https://www.home-assistant.io/integrations/diagnostics/) (supported from Hass v2022.2):

- All devices: Configuration > [Integrations](https://my.home-assistant.io/redirect/integrations/) > **Oversight Android TV Notifications** > 3 dots > Download diagnostics
- One device: Configuration > [Devices](https://my.home-assistant.io/redirect/devices/) > Device > Download diagnostics

*There is no private data, but you can delete anything you think is private.*