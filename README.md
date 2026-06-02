# HA Dashboard Manager

Automatic kiosk rotation manager for Home Assistant. Rotate through dashboards on a per-dashboard timer, manage the rotation from a UI, and use a browser_mod popup for nav controls that works across all themes including HA-LCARS.

## Features

- **Rotation** — timer-based, per-dashboard display times, auto-resumes after 5-minute pause
- **Persistent config** — rotation list stored as JSON in an `input_text` entity; HA restores it automatically across restarts with no race condition and no file to edit
- **Dashboard picker** — enumerates all dashboards configured in HA; select from a dropdown to add to rotation
- **Nav overlay** — browser_mod popup with Prev / Play-Pause / Stop / Next; LCARS-safe (uses custom:button-card, not card-mod on buttons)

## Dependencies (all via HACS)

| Component | Purpose |
|---|---|
| browser_mod | Navigate kiosk browser, show popup overlay |
| card-mod | UI card styling |
| custom:button-card | Nav overlay buttons (LCARS-safe sizing) |

## Installation

### 1. Copy packages

Copy the four files from `packages/` to `/config/packages/`:
- `dashboard_manager_core.yaml`
- `dashboard_manager_persistence.yaml`
- `dashboard_manager_rotator.yaml`
- `dashboard_manager_nav.yaml`

Ensure your `configuration.yaml` includes:
```yaml
homeassistant:
  packages: !include_dir_named packages
```

### 2. Add the dashboard UI

Copy `dashboards/dashboard_manager_ui.yaml` to `/config/dashboards/`.

Add to `configuration.yaml` under `lovelace.dashboards`:
```yaml
lovelace:
  dashboards:
    dashboard-manager:
      mode: yaml
      title: "Dashboard Manager"
      icon: mdi:monitor-dashboard
      show_in_sidebar: true
      filename: dashboards/dashboard_manager_ui.yaml
```

### 3. Create a Long-Lived Access Token

The dashboard enumeration sensor reads `/config/.storage/lovelace_dashboards` via a `command_line` sensor — no token needed for that. The REST API is not used.

### 4. Set your browser ID

In the Dashboard Manager UI, set **Target Browser ID** to match your kiosk's browser_mod ID (default: `kitchen_kiosk`). Find your browser's ID at **Settings → Devices & Services → Browser Mod**.

### 5. Restart Home Assistant

After restart:
- If this is a fresh install: add dashboards via the UI; they auto-save
- If migrating from the old file-based system: click **Settings → Developer Tools → Services**, call `script.dashboard_manager_save_to_json` once to bootstrap the JSON store from the current `input_select` options

## Removing old static nav from dashboards

If you previously added nav button cards directly to individual dashboards, remove them after installing the popup nav. The following storage-mode dashboards were found to have static nav cards:

- dashboard_cameras2
- dashboard_main
- dashboard_opnsense
- dashboard_temperature
- dashboard_weather
- lcars_images
- live_camera_test
- ninjamonkey_homelab
- swimming_pool
- system_monitors
- ubuntu_box_monitor
- uptime_kuma

For each: open the dashboard in the HA UI editor, find the nav card (buttons calling `script.dashboard_nav_previous` / `script.dashboard_nav_next`), and delete it.

## Data format

The rotation list is stored as JSON in `input_text.dashboard_manager_json`:

```json
[
  {"label": "Cameras", "path": "/live-camera-test/cameras", "display_time": 30},
  {"label": "News", "path": "/dashboard-news/0", "display_time": 60}
]
```

The `input_select.dashboard_rotation` holds the same data as pipe-delimited strings for runtime use:
```
Cameras | /live-camera-test/cameras | 30
```

## LCARS theme note

HA-LCARS 4.x (with card-mod 4.x) changed the CSS element selector from `ha-card` to `hui-card`. Any card using `card_mod: style: ha-card { height: Xpx }` to constrain button height will break — the LCARS theme's flex styles take over and stretch buttons full-height (as seen in the screenshot).

The nav overlay uses `custom:button-card` with `styles.card` instead of card-mod, which is isolated from theme CSS selectors entirely. Height and sizing are always respected regardless of active theme.
