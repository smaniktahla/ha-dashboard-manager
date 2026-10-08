# HA Dashboard Manager
Turn your HA browser session into a rotation of dashboards you select! Camera feeds, news, weather, smart home device status, I've even got my CPAP metrics (CPAPs are sexy, shut up). 

Automatic kiosk rotation manager for Home Assistant. Rotate through dashboards on a per-dashboard timer, and manage the rotation from a UI. Includes a single, reusable nav overlay ([`navbar-card`](https://github.com/joseluis9595/lovelace-navbar-card)) with Previous / Play-Pause / Stop / Next / a live countdown / a jump-to-manager button — the exact same card pasted into every dashboard, toggleable per-dashboard from the UI. See [Nav overlay](#nav-overlay) for why this replaced two earlier approaches that didn't hold up.

## Features

- **Rotation** — timer-based, per-dashboard display times, auto-resumes after 5-minute pause (actually resumes the interrupted countdown, not a fresh one — see [Pausing rotation](#pausing-rotation-from-other-automations)), auto-starts on HA boot
- **Persistent config** — rotation list stored as plain text in `/config/dashboard_rotation.txt`, one dashboard per line; HA restores it automatically across restarts with no race condition and no 255-character limit
- **Dashboard picker** — enumerates all dashboards configured in HA; select from a dropdown to add to rotation. Only sees storage-mode (UI-created) dashboards — YAML-mode dashboards declared under `lovelace.dashboards` in `configuration.yaml` (like this one, and House Floorplan-style dashboards) don't show up in that dropdown at all, since they're never written to `.storage/lovelace_dashboards`, which is what the enumeration sensor reads. Add those via the "Add Dashboard Manually" form instead.
- **Voice-launched dashboards** — give each dashboard a few spoken *topics* ("pool", "internet", "weather"); when a voice query matches, the kiosk jumps to that dashboard for a short hold and then resumes rotation. One dashboard per topic. See [Voice topics](#voice-topics).
- **Nav overlay** — `navbar-card`, one identical block pasted into every dashboard; Previous/Next read the same rotation list Dashboard Manager maintains, so there's no separate list to keep in sync. Toggle visibility per-dashboard from the "Nav Bar on This Dashboard" switch.

<img width="1687" height="1206" alt="image" src="https://github.com/user-attachments/assets/23d305ce-dbff-40e7-8d5f-1f6f7a650273" />
<img width="1651" height="1202" alt="image" src="https://github.com/user-attachments/assets/0a8ad4ff-dae8-4f34-8603-98db712cbe67" />

## Dependencies (all via HACS)

| Component | Purpose |
|---|---|
| browser_mod | Navigate the kiosk browser for automatic (timer-driven) rotation |
| card-mod | UI card styling |
| navbar-card | Nav overlay — see [dashboards/navbar_card_snippet.yaml](dashboards/navbar_card_snippet.yaml) |
| custom:button-card | Toggle switch on the Dashboard Manager UI itself |

## Installation

### 1. Copy packages

Copy the package files from `packages/` to `/config/packages/`:
- `dashboard_manager_core.yaml`
- `dashboard_manager_persistence.yaml`
- `dashboard_manager_rotator.yaml`
- `dashboard_shell_commands.yaml`
- `dashboard_manager_voice.yaml` (optional - only needed for [Voice topics](#voice-topics) / `script.dashboard_show`)

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

In the Dashboard Manager UI, set **Target Browser ID** to match your kiosk's browser_mod ID (default: `kitchen_kiosk`). This is only used for the *automatic* timer-driven rotation on that one unattended display — it has nothing to do with the nav overlay below, which controls whichever screen you're looking at directly. Find your browser's ID at **Settings → Devices & Services → Browser Mod**.

### 5. Add the nav overlay to your dashboards

Install `navbar-card` via HACS (or manually — copy `navbar-card.js` to `<config>/www/` and register it as a Lovelace resource with URL `/local/navbar-card.js`, type `module`).

Paste the card from [`dashboards/navbar_card_snippet.yaml`](dashboards/navbar_card_snippet.yaml) into every dashboard's view `cards:` list. It's the identical block everywhere — nothing to customize per-dashboard except changing the last route's `url` if your Dashboard Manager page lives somewhere other than `/dashboard-manager/0`. Read the comments at the top of that file first — panel views and `type: sections` views need small structural adjustments (wrap-in-a-vertical-stack, or add to a section instead of the top-level `cards:` list) that are explained and shown there.

### 6. Restart Home Assistant

After restart:
- Add dashboards via the UI; each change auto-saves to `/config/dashboard_rotation.txt` ~2 seconds later
- On the next boot the rotation list is restored automatically, and rotation auto-starts if it was enabled (and not paused)

## Nav overlay

Two earlier approaches to a floating/global nav overlay didn't hold up under real testing, in case you're tempted to reach for either one instead of `navbar-card`:

**A hand-rolled `position: fixed` card_mod overlay pasted into each dashboard.** `position: fixed` only centers against the true viewport if no ancestor element has its own CSS transform. Any dashboard whose view wraps its cards in a layout card (`custom:grid-layout`, `custom:layout-card`) or uses a `type: sections` view becomes a new containing block for that fixed element — the bar drifts, shrinks, or overlaps content depending on that specific dashboard's internal layout. It "worked" on some dashboards and silently broke on others. Not a CSS tweak away from fixed — a structural dead end, because the fragility is inherent to which dashboards happen to use a layout wrapper, which changes over time as you add dashboards.

**`dashboard_manager_nav.yaml`, a `browser_mod` popup with Prev/Play-Pause/Stop/Next.** The popup mechanism itself works — opens, dismisses, addresses the right browser. But custom card content (`custom:button-card`, stock `button`, `tile`) rendered *inside* a browser_mod popup collapsed to zero height on testing — title bar shows, body stays empty. Only `markdown` rendered correctly in that same slot. That's a specific incompatibility between whatever card-creation path browser_mod's popups use and some combination of HA/card-mod/theme versions, not something fixable with more styling. Confirmed by testing three unrelated card implementations side-by-side, all failing identically. The file is kept in git history for reference but removed from `packages/` — don't re-add it without expecting to hit the same wall, unless something upstream has since changed.

`navbar-card` sidesteps both problems: it's a real card living in a dashboard's own view (no `position: fixed` escaping a wrapper needed at all, so the containing-block problem above doesn't apply), and it renders its own content directly rather than going through browser_mod's popup card-creation path.

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

Each line is `Label | path | seconds`, optionally followed by `| nav-flag | topics`
(`true`/`false` for the nav overlay, then comma-separated [voice topics](#voice-topics)).
Entries without the extra fields keep working unchanged. Scripts that rewrite an
entry (display time, nav toggle, topics) carry every field through.

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

Pausing calls `timer.pause` (not `timer.cancel`) on `timer.dashboard_rotation_timer`, which
preserves the remaining time; unpausing calls `timer.start` with no `duration`, which HA's
timer domain resumes from wherever it was paused rather than restarting a fresh window. If
you're pausing/resuming this timer from your own scripts directly (instead of going through
`input_boolean.dashboard_rotation_paused`), use the same pair of calls to get the same
behavior — `timer.cancel` + a fresh `timer.start` will restart the countdown instead of
resuming it.

Separately, `input_boolean.dashboard_rotation_enabled` is the master on/off switch (distinct
from *paused*) — `script.dashboard_rotation_stop` turns rotation off entirely and cancels the
timer; nothing auto-restarts it until `script.dashboard_rotation_start` runs again. If your
nav overlay's countdown pill is stuck on `idle` and pause/resume doesn't seem to do anything,
check this boolean before assuming something's broken.

## Voice topics

Voice assistants are good at *answering*; a wall display is good at *showing*.
This lets a spoken question put the matching dashboard on screen: ask about the
pool and the pool cameras come up, ask about the internet and the firewall stats
appear, then the display goes back to rotating.

### Setting topics

In **Dashboard Manager → Manage Selected Dashboard**, select a dashboard, type
comma-separated topics into **Voice topics**, and press **Save Topics**
(`script.dashboard_rotation_set_topics`). Topics are stored as the 5th field of
that dashboard's rotation entry, e.g.:

```
Swimming Pool | /swimming-pool/cameras | 30 | true | pool, swimming
OPNsense | /dashboard-opnsense/opnsense-stats | 30 | true | internet, wan, network connection
```

- Topics are lowercased and reduced to letters, digits and spaces. Multi-word topics are fine.
- **A topic can belong to only one dashboard.** Saving a topic that another dashboard already uses is rejected with a notification naming the conflict; nothing is changed.
- Clear a dashboard's topics by saving an empty field.
- Only dashboards in the rotation list can carry topics.

### How a query is matched

`script.dashboard_show_for_utterance` takes the text and looks for each topic as a
whole word (a trailing "s" is also accepted, so `camera` matches "cameras"). If several
dashboards match, the **longest topic wins** (the most specific), then the one that
appears earliest in the sentence, so at most one dashboard is launched. No match does
nothing.

The chosen dashboard is shown with `script.dashboard_show`, which:
1. turns on `input_boolean.dashboard_rotation_paused` (the same documented pause hook as above),
2. navigates the Target Browser to the dashboard,
3. holds for `hold_seconds` (default **45**),
4. calls `script.dashboard_rotation_resume`, which unpauses and advances to the next dashboard.

You can also call `script.dashboard_show` directly with either a rotation name or a
path: `dashboard: weather` or `dashboard: /dashboard-weather/0`, plus an optional
`hold_seconds`.

### Feeding it queries

An automation listens for the event **`needle_voice_utterance`** with `{text: "..."}`
and runs the matcher. Fire it from whatever handles your voice queries.

With HA's built-in Assist, a catch-all [sentence trigger](https://www.home-assistant.io/docs/automation/trigger/#sentence-trigger)
can do it for the phrases you care about:

```yaml
automation:
  - alias: "Voice: show a dashboard"
    trigger:
      - platform: conversation
        command:
          - "show me {topic}"
          - "what's the {topic}"
    action:
      - event: needle_voice_utterance
        event_data:
          text: "{{ trigger.sentence }}"
```

With a custom conversation agent, fire the same event from code, for example
`hass.bus.async_fire("needle_voice_utterance", {"text": user_input.text})`. In the
author's setup the router fires it only for informational questions it hands to the
LLM (not for device commands such as "turn off the pool light", which would otherwise
pop up the pool dashboard), once when the question arrives and again when the
answer comes back so the dashboard is still showing when the answer is spoken.

> **Gotcha for anyone extending these scripts:** HA strips leading/trailing whitespace
> from rendered template variables, so a variable holding `" | topics"` silently loses
> its leading space and glues fields together (`true| pool`). Build entries with
> `[...] | join(' | ')` instead of concatenating a suffix variable.

## LCARS theme (Personal Note)
I like running the LCARS theme on my kiosk display, because it's fun and I like Star Trek.

HA-LCARS 4.x (with card-mod 4.x) changed the CSS element selector from `ha-card` to `hui-card`. Any card using `card_mod: style: ha-card { height: Xpx }` to constrain button height will break — the LCARS theme's flex styles take over and stretch buttons full-height (as seen in the screenshot).

The nav overlay uses `custom:button-card` with `styles.card` instead of card-mod, which is isolated from theme CSS selectors entirely. Height and sizing are always respected regardless of active theme.
