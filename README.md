# HA Dashboard Manager
Turn your HA browser session into a rotation of dashboards you select! Camera feeds, news, weather, smart home device status, I've even got my CPAP metrics (CPAPs are sexy, shut up). 

Automatic kiosk rotation manager for Home Assistant. Rotate through dashboards on a per-dashboard timer, and manage the rotation from a UI. Optionally includes a browser_mod popup for nav controls that works across all themes including HA-LCARS (see [Nav overlay: current status](#nav-overlay-current-status) — not enabled on the reference install).

## Features

- **Rotation** — timer-based, per-dashboard display times, auto-resumes after 5-minute pause, auto-starts on HA boot
- **Persistent config** — rotation list stored as plain text in `/config/dashboard_rotation.txt`, one dashboard per line; HA restores it automatically across restarts with no race condition and no 255-character limit
- **Dashboard picker** — enumerates all dashboards configured in HA; select from a dropdown to add to rotation
- **Nav overlay (optional)** — browser_mod popup with Prev / Play-Pause / Stop / Next; LCARS-safe (uses custom:button-card, not card-mod on buttons)

<img width="1687" height="1206" alt="image" src="https://github.com/user-attachments/assets/23d305ce-dbff-40e7-8d5f-1f6f7a650273" />
<img width="1651" height="1202" alt="image" src="https://github.com/user-attachments/assets/0a8ad4ff-dae8-4f34-8603-98db712cbe67" />

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
- `dashboard_shell_commands.yaml`

`dashboard_manager_nav.yaml` (the browser_mod popup nav overlay) is included
for reference but **not currently deployed** on the reference install — see
[Nav overlay: current status](#nav-overlay-current-status) below before
adding it.

Also copy `dashboard_manager/read_rotation.sh` to `/config/dashboard_manager/`
and make it executable (`chmod +x`) — the persistence sensor shells out to it.

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

## Nav overlay: current status

`dashboard_manager_nav.yaml` implements a `browser_mod` popup with Prev /
Play-Pause / Stop / Next buttons, meant to float over whatever dashboard is
currently showing. On the reference install this package is **not currently
loaded** — the `script.dashboard_nav_show` / `dashboard_nav_hide` entities
show up as `unavailable` in HA, left over from a prior deployment. The
decision (2026-06-02) was to rely on the Dashboard Manager UI's own transport
controls instead, since per-dashboard nav cards rendered inconsistently across
panel/strategy/single-iframe dashboards under some themes (see the LCARS note
below for the specific CSS conflict that motivated `custom:button-card` in the
first place). If you want the floating overlay back, the file is still here
and should still work — just re-add it to `/config/packages/` and confirm the
`browser_mod` / `custom:button-card` dependencies are installed.

## How persistence works

The rotation list lives in `input_select.dashboard_rotation` at runtime, as
pipe-delimited option strings:

```
Cameras | /live-camera-test/cameras | 30
```

These are persisted to disk as plain text in `/config/dashboard_rotation.txt`,
**one dashboard per line** — readable, and `git diff`-friendly if you keep
your own copy under version control:

```
Cameras | /live-camera-test/cameras | 30
News | /dashboard-news/0 | 60
```

An earlier version of this joined all entries onto a single line with a
`~~~` delimiter instead of real newlines, to dodge a JSON-encoding problem
(see below). That traded away human/git readability for no real benefit —
`dashboard_manager/read_rotation.sh` now does the JSON-safe encoding instead,
so the on-disk file can stay one-entry-per-line.

| Direction | Mechanism |
|---|---|
| **Save** | The `dashboard_manager_autosave` automation fires ~2 s after the `input_select` changes, calling `script.dashboard_manager_save_to_json`, which joins the options with a real newline (`\n`) and writes them via `shell_command.write_dashboard_rotation`. |
| **Load** | `sensor.dashboard_rotation_text` runs `dashboard_manager/read_rotation.sh`, which reads the file line-by-line and builds `{"data": "..."}` with each line break emitted as a literal two-character `\n` escape — real newline bytes can't go raw inside a JSON string, but HA's JSON decoder turns `\n` right back into a real newline once it parses the attribute. On the HA `start` event, `script.dashboard_manager_load_from_json` reads that attribute, splits on `\n`, and repopulates the `input_select`. |

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

`read_rotation.sh` uses only `sh` builtins (`read`/`printf`) — no `sed`/`awk`/
`tr` — since the HA Core container isn't guaranteed to have them installed.

## Pausing rotation from other automations

If you want another automation (a camera alert popup, a doorbell announcement,
etc.) to pause rotation while it does something and resume it afterward, target
**`input_boolean.dashboard_rotation_paused`** — turn it `on` to pause, `off` to
resume. This is the only supported pause mechanism; earlier iterations of this
project used a different, since-removed `input_boolean` for the same purpose,
and automations still pointed at that dead entity fail silently (HA logs a
`WARNING: Referenced entities ... missing or not currently available` but
otherwise no error) — the popup still shows, but rotation never actually pauses
underneath it. If you're migrating from an older setup, grep your
`automations.yaml` for the old entity name and repoint it at
`dashboard_rotation_paused`, flipping `turn_on`/`turn_off` since the semantics
are inverted (old entity being "on" meant rotation *enabled*; the new one being
"on" means rotation *paused*).

## LCARS theme (Personal Note)
I like running the LCARS theme on my kiosk display, because it's fun and I like Star Trek.

HA-LCARS 4.x (with card-mod 4.x) changed the CSS element selector from `ha-card` to `hui-card`. Any card using `card_mod: style: ha-card { height: Xpx }` to constrain button height will break — the LCARS theme's flex styles take over and stretch buttons full-height (as seen in the screenshot).

The nav overlay uses `custom:button-card` with `styles.card` instead of card-mod, which is isolated from theme CSS selectors entirely. Height and sizing are always respected regardless of active theme.
