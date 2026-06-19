# HA Dashboard Manager

Automatic kiosk rotation manager for Home Assistant. Rotate through dashboards on a per-dashboard timer, manage the rotation from a UI, and use a browser_mod popup for nav controls that works across all themes including HA-LCARS.

## Features

- **Rotation** — timer-based, per-dashboard display times, auto-resumes after 5-minute pause, auto-starts on HA boot
- **Persistent config** — rotation list stored as plain text in `/config/dashboard_rotation.txt`; HA restores it automatically across restarts with no race condition and no 255-character limit
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

Copy the package files from `packages/` to `/config/packages/`:
- `dashboard_manager_core.yaml`
- `dashboard_manager_persistence.yaml`
- `dashboard_manager_rotator.yaml`
- `dashboard_manager_nav.yaml`
- `dashboard_shell_commands.yaml`

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
- Add dashboards via the UI; each change auto-saves to `/config/dashboard_rotation.txt` ~2 seconds later
- On the next boot the rotation list is restored automatically, and rotation auto-starts if it was enabled (and not paused)

## How persistence works

The rotation list lives in `input_select.dashboard_rotation` at runtime, as
pipe-delimited option strings:

```
Cameras | /live-camera-test/cameras | 30
```

These are persisted to disk as plain text in `/config/dashboard_rotation.txt`,
with options joined by a `~~~` delimiter:

```
Cameras | /live-camera-test/cameras | 30~~~News | /dashboard-news/0 | 60
```

| Direction | Mechanism |
|---|---|
| **Save** | The `dashboard_manager_autosave` automation fires ~2 s after the `input_select` changes, calling `script.dashboard_manager_save_to_json`, which joins the options with `~~~` and writes them via `shell_command.write_dashboard_rotation`. |
| **Load** | `sensor.dashboard_rotation_text` reads the file (wrapping the text in trivial JSON so it lands in an attribute, sidestepping HA's 255-char *state* limit). On the HA `start` event, `script.dashboard_manager_load_from_json` reads that attribute, splits on `~~~`, and repopulates the `input_select`. |

**Why plain text, not JSON?** The option strings contain no double-quotes, so
storing them verbatim avoids two traps that broke earlier JSON-based attempts:
shell-quoting corruption when the JSON passes through `shell_command`, and
RestrictedPython's blocked file I/O inside `python_script`. The 255-character
state limit that rules out an `input_text` store does **not** apply to
`command_line` sensor *attributes*.

You'll need a matching `shell_command` (see `dashboard_shell_commands.yaml` in
your `/config/packages/`):

```yaml
shell_command:
  write_dashboard_rotation: sh -c 'printf "%s" "$0" > /config/dashboard_rotation.txt' "{{ content }}"
```

## LCARS theme (Personal Note)
I like running the LCARS theme on my kiosk display, because it's fun and I like Star Trek. 

HA-LCARS 4.x (with card-mod 4.x) changed the CSS element selector from `ha-card` to `hui-card`. Any card using `card_mod: style: ha-card { height: Xpx }` to constrain button height will break — the LCARS theme's flex styles take over and stretch buttons full-height (as seen in the screenshot).

The nav overlay uses `custom:button-card` with `styles.card` instead of card-mod, which is isolated from theme CSS selectors entirely. Height and sizing are always respected regardless of active theme.
