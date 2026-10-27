# Debian dotfiles

Personal configuration collected from Debian 13.6. Applications, secrets,
installed plugins and session data are not included.

## Quick setup on a personal computer

See [install/README.md](install/README.md) for a Debian 13 installation without
work configuration. `bash install-private.sh` previews what it does;
`bash install-private.sh --apply` installs on **the new computer**.
This uses private configuration copies and automatic backups instead of
the symlinks described in the manual instructions below.

## Files and destinations

| In the repository | Destination |
| --- | --- |
| `i3/` | `~/.config/i3/` |
| `nvim/` | `~/.config/nvim/` |
| `alacritty/` | `~/.config/alacritty/` |
| `scripts/` | `~/.config/scripts/` |
| `lazygit/` | `~/.config/lazygit/` |
| `rofi/` | `~/.config/rofi/` |
| `flameshot/` | `~/.config/flameshot/` |
| `bash/.bashrc` | `~/.bashrc` |
| `bash/.bash_aliases` | `~/.bash_aliases` |
| `bash/.profile` | `~/.profile` |
| `tmux/.tmux.conf` | `~/.tmux.conf` |

The Lazygit configuration file is currently empty, so it uses the defaults.

## Installation

1. Install Git and clone the repository to `~/code/dotfiles-debian`.
2. Install the applications listed below.
3. Compare existing configuration with the table and back it up before
   replacing it. Debian normally creates `.bashrc` and `.profile` already.
4. Symlink the files/directories from the repository to the listed destinations.
   For example, when the destination does not already exist:

   ```sh
   mkdir -p ~/.config
   ln -s "$HOME/code/dotfiles-debian/nvim" "$HOME/.config/nvim"
   ```

5. Install TPM if `~/.tmux/plugins/tpm` is missing:

   ```sh
   git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
   ```

   Start tmux and press `Ctrl-a`, then `I` to install plugins.
6. Start Neovim and run `:Lazy restore` to restore plugin versions from
   `lazy-lock.json`. Mason and Treesitter install additional tools/parsers;
   network access and build tools are required. Run `:checkhealth` afterwards.
7. Run `pnpm install --frozen-lockfile` in
   `~/.config/scripts/conventional-commits` for the `cc` alias.
8. Create local secrets as described below, adjust hardware settings and
   select i3 at login.

On the original computer, all configuration in the table is symlinked to the
repository. Originals are backed up under `~/.local/state/dotfiles-backups/`.
Git identity and secrets are managed separately outside the repository.

## Dependencies

This list is based on the configuration, not a complete export of installed
packages. Installation on a fresh computer has not yet been verified.

- Desktop: i3 with gaps support, i3blocks and its standard scripts, Alacritty,
  Rofi, Flameshot, dex, xss-lock, i3lock, NetworkManager/nm-applet, pactl,
  brightnessctl, xset, setxkbmap, xinput, xrandr, xdotool and Dunst (`dunstctl`).
- Shell and development: Bash, bash-completion, Git, tmux, fzf, ripgrep,
  Neovim, lazygit, Starship, NVM/Node.js, pnpm and Go.
- Delayed suspend on lid close: `python3-dbus` and `python3-gi`.
- Neovim/plugins: a C compiler and make, Python with virtual environment support,
  unzip, curl, an X11 clipboard tool such as xclip, and xmllint.
- The lock screen script uses ImageMagick's `import` and `convert`.
- Fonts: MesloLGL Nerd Font Propo for Alacritty and i3, and MesloLGS Nerd Font
  Mono for Rofi. Install the fonts separately and run `fc-cache -f`.
- i3 has rules for Chrome, Slack and Spotify. Spotify autostart is currently commented out.

## Local secrets

`.bashrc` loads `~/.bash_secrets` if it exists. Keep this file outside the
repository with permissions `600`. Create it on a new computer with:

```sh
(umask 077; touch "$HOME/.bash_secrets")
chmod 600 "$HOME/.bash_secrets"
```

Store local environment variables containing secret values there. Never copy
real tokens into the repository. `.gitignore` also excludes `.bash_secrets` files.
SSH keys are installed separately; the `persist-ssh` alias expects `~/.ssh/id_ed25519`.

## Do not disturb in i3blocks

Left-click `🔔` to pause Dunst notifications, including Chrome desktop
notifications. The button changes to a yellow `🔕`. Click again to resume;
queued notifications may then appear. Audio from websites is unaffected.
Status is read from Dunst every two seconds, so changes made through
`dunstctl set-paused true/false` are reflected too. `⚠` means the status
could not be read or the toggle failed.

## Västtrafik journeys in i3blocks

`i3/vasttrafik` searches complete journeys between selectable stops. The default
is **Kaptensgatan → Trollhättan resecentrum**, via Göteborg Central or
Gamlestaden Station. Change the origin and destination in Rofi. The status bar
shows only `🚋`, `🚋 !` for service alerts/delays, or `🚋 ?` for fetch errors/stale
information. Requires Python 3 and Rofi, with no additional Python packages.

The journey planner's interface is in Swedish. Menu labels and example output
below retain their actual wording so they can be matched to the interface.

1. Subscribe to **Planera Resa v4** in the
   [Västtrafik portal](https://developer.vasttrafik.se/apis/13/v4).
2. Run `~/.config/i3/vasttrafik --setup`. Client ID and secret are entered
   without echo and saved with permissions `600` in
   `~/.config/vasttrafik/config.json`, outside the repository. An existing
   file is not overwritten. Tokens are fetched and renewed automatically.
3. Try `~/.config/i3/vasttrafik --now`. Restart i3 with `Mod+Shift+r` if the
   block is not already in the status bar. Script changes take effect the
   next time the block runs.

Example Rofi entry with fictional times:
`7 15:12 från Kaptensgatan, läge A → V-TÅG 15:40 från Göteborg Central, spår 7 → ~16:15 (8m) !`

This means tram 7 from stop position A at 15:12, a train from Centralen at 15:40,
arrival in Trollhättan at 16:15, and an eight-minute connection margin **after
the API's estimated walking time**. `~` means a leg uses the timetable instead
of a real-time forecast. `!` on a journey entry indicates a delay. The icon's
`!` only applies to delays or cancellations from 30 minutes before you need
to leave the origin, including your configured time to reach the stop. This
is based on the scheduled departure, so a delay does not postpone the warning.
Previously fetched information remains available in the menu before this
window; connection margins are shown in Rofi.

When the panel shows `!`, open the menu and select the first entry:
**! Visa varningen – bevakad resa** (or **sökresultaten** without active tracking).
It shows the unread delays/cancellations behind the exclamation mark, along
with the fetch time and an indication of stale information. Simply opening
and closing the main menu does not mark warnings as read.

After opening and closing the warning list, a tracked journey or journey
details, the warnings shown there are marked as read. The panel's `!`
disappears on the next update (normally within a minute), provided no unread
warnings remain. A changed delay, cancellation or another affected departure
can trigger `!` again. Messages remain in the menu. Read markers are stored
locally for the day and do not affect `?`, reminders or API calls.

- **Ctrl+Esc** (also Super+Esc) → **Västtrafik – resor:** open the journey planner.
  From a terminal: `~/.config/i3/vasttrafik --menu`.
- **Pausa resten av dagen:** pause journey fetching and reminders until the
  next calendar day. The panel shows `🚋 ⏸`. Open the menu and select
  **Återuppta** to resume earlier. From a terminal:
  `~/.config/i3/vasttrafik --pause`. The pause is stored locally and survives restarts.
- **Left-click:** open the menu immediately, without API calls. Cached upcoming
  journeys are shown if available; stale information is marked. Searches taking
  more than 0.3 seconds show a waiting message in Rofi using the menu theme.
  It closes automatically before the results menu, including on errors. This
  is a waiting message, not a percentage estimate. Select an arrival time or
  **Åk så snart som möjligt** to fetch journeys.

Each departure shows its stop/station and stop position or platform, including
transfers and tracked journeys. The current platform takes precedence;
missing information is shown as “spår/läge ej angivet”.

- **Select a journey:** read its legs, direction, stop positions/platforms,
  walking times and delays as separate entries. Close the details to return.
- **Framme senast…:** the default menu option. Press Enter, then Enter again
  for the default **Båda**, and enter when you want to reach the final destination.
  For Trollhättan, this means **home**, allowing 10 minutes from the travel centre.
  For example, home by 17:00 searches for arrival at the station by 16:50.
  Results show both station arrival and the estimated time at the final
  destination. For routes other than Kaptensgatan–Trollhättan, the time field opens directly.
- **Uppdatera resorna:** refresh both active tracking and search results, keeping
  the requested time, transfer station and number of alternatives. Caching
  (at least 60 seconds) and API error backoff still apply. Fetch time appears
  in the menu header; an open list does not refresh itself.
- **Uppdatera bevakad resa:** refresh only the selected vehicle departures and
  open their times and specific warnings. Works before automatic tracking
  starts too, with the same caching and API error backoff.
- **Hem från jobbet / Till jobbet:** select Kaptensgatan–Trollhättan or the
  reverse direction. **Byt riktning** reverses the current route.
- **Hem från…:** select only the origin stop, such as Göteborg Central. The
  destination is Trollhättan resecentrum, with your saved travel time from the
  station to home. This is temporary; the standard planner can also show direct trains.
- **Annan resa…:** choose a temporary origin and destination, such as Ullevi to
  Trollhättan. The saved default route and background search remain unchanged.
  Reversing the direction also applies only to the open menu.
- **Inställningar…:** set **Tid till hållplats…** (including your own margin)
  and **Tid från hållplats till mål…**, separately for each stop name and direction.
  Travel from home to Trollhättan resecentrum and from the station to home
  defaults to 10 minutes. Other times default to 0 until configured; the menu
  indicates when time to the stop is not included. No map requests are needed.
  **Spara denna sträcka som standard** is an explicit choice.
- **Åk så snart som möjligt:** return to upcoming journeys. Clicking the icon
  again always starts with upcoming journeys for the default route; a selected
  arrival time applies only to the open menu. Middle- and right-click open the same menu.

Journey entries show the estimated time at the final destination and when to
leave the origin, including upcoming departures. Departures that cannot be
reached within the configured time to the stop are filtered out during the search.

Personal travel times and the explicitly saved default route are stored in
`~/.config/vasttrafik/route.json`, separately from API credentials. Origin,
destination and time to the first stop are included in the result cache key.

Select a journey, then **Bevaka den här resan**, to have the panel update those
specific vehicle departures. Tracking replaces the normal background search
and also works outside 15:00–17:00. Detail references are reused per journey:
normally two detail requests per update for a separately matched tram and train,
or one for a complete journey from the planner. If a departure is missing from
the detail response, `?` is shown; no other departure is selected automatically.

Delays can be followed after boarding too. The tracked journey shows
**Lämna senast** first, based on the scheduled departure and configured time
to reach the stop. A reported delay does not move the leave-by time later.
The same rule applies to journey entries. Departure and arrival are shown as,
for example, `beräknad 15:40 (+2 min; tidtabell 15:38)`. Missing forecasts are
stated explicitly. The home arrival time indicates whether it uses a forecast
or timetable plus the final leg. A cancelled leg or an impossible connection
suppresses the home arrival estimate and prompts you to find another journey.

Journey entries are concise: `Hemma ≈16:48 | Gå 15:22`, followed by departures,
stops and platforms. The old saved journey entry is not mixed with updated
times. **Visa bevakad resa** reads the cache without network requests;
**Avsluta bevakning** returns to normal behaviour.

Automatic tracking waits without API requests until 30 minutes before you
need to leave. The icon is dimmed while waiting; normal background searches
do not resume during this wait. Updates start on the first panel tick after
the threshold. Without selected tracking, the normal 15:00–17:00 fetch window
still applies, but the exclamation mark is limited to journeys that require
leaving soon.

Two minutes before the scheduled **Lämna senast** time, a one-time notification
is sent: “Dags att packa ihop datorn – gå senast HH:MM”. The panel's minute
update checks the time before any network requests, so the notification can
arrive up to roughly one minute after the two-minute threshold. No notification
is sent after the leave-by time. Changing or ending tracking replaces/disables
the reminder. The computer and panel must be running. The notification uses
`notify-send` and requires no API requests; multiple monitors share the same
one-time marker.

The reminder reads the latest saved traffic status: for a cancelled journey
or impossible connection, it asks you to choose another journey. If information
is missing or more than three minutes old, it asks you to check the traffic status.
Tracking expires 30 minutes after the last known estimated arrival at the final
destination, no earlier than the time recorded when selected. A delay can extend
tracking by at most three hours beyond the original end time, and tracking
always ends when the date changes. References are valid only for the same day.
The selection is stored privately in `watch.json` without API keys.

Terminal commands:

```sh
~/.config/i3/vasttrafik --text         # upcoming journeys for the default route, without Rofi
~/.config/i3/vasttrafik --diagnostics  # cache age and statistics for the latest search
~/.config/i3/vasttrafik --usage        # local usage grouped by feature, day and hour
```

Local usage logging is enabled from installation. Menu openings, fixed menu
choices, displayed journey details, tracking starts/stops, pauses and manual
terminal calls are timestamped in `~/.local/state/vasttrafik/usage.jsonl`
(or under `$XDG_STATE_HOME`). The file is created with permissions `600` and
the directory with `700`. No stops, entered times, free text, API keys or API
responses are logged, and nothing is transmitted. Automatic panel updates are
not logged. Menu choices record what you clicked even if you later cancel the
dialog; completed arrival searches and started tracking have their own events.
The number of events therefore is not the number of journeys. The log is kept
until deleted, and `--usage` summarizes the entire file without recording usage
itself or making API calls. Set `VASTTRAFIK_TRACKING=0` in the application's
environment to disable logging. Log write errors do not affect the planner.

`--text` searches manually even outside the time window, respects cache/backoff,
and shows fetch time and warnings. `--diagnostics` makes no API calls; its JSON
output shows the mode (tracking/upcoming journeys), cache age, HTTP request
count, subquery cache hits and duration of the latest successful fetch.
Statistics include any token and stop lookup requests. No keys, tokens or raw
API responses are printed.

Between Kaptensgatan and Trollhättan, results combine a tram and a direct train
in both directions, with a choice of Centralen/Gamlestaden. For other stops,
the planner allows all transport modes, including direct journeys and multiple
transfers. Walking time is deducted at each transfer; the minute count in the
journey entry is the smallest margin after walking. Details explain every transfer.

From Kaptensgatan to Trollhättan, direct trains are searched separately from
Centralen and Gamlestaden, then trams are matched to the train's actual platform.
At least five minutes of margin after walking is required. The tram's current
arrival plus walking time is used if the API's walking-leg arrival is earlier.
The same train may appear from both stations; Centralen comes first to make
earlier boarding easier. The two station searches run concurrently (at most
two parallel requests) to reduce waiting. This does not change the request
count or cache lifetime.

With a selected arrival time, the first result is a train arriving by that time.
**Ladda en tidigare** and **Ladda en senare** extend the list one train at a
time on either side of the arrival time. Existing alternatives are retained.
A new arrival time resets the list to one train before that time. Later arrivals
are clearly marked with the number of minutes after the requested time.
`17` is interpreted as `17:00`. Connections to the same train and boarding
station are grouped: a margin of at least five minutes is preferred when
available, then fewer legs, then the latest departure. If the first tram
response only offers extra transfers, an earlier page is checked for a direct
tram within the same two-page limit. For journeys without trains, identical
vehicle departures are grouped. `Inget förslag` means the search results contain
no suitable journey, not that all services are unavailable. The planner is not
a complete departure board of missed or cancelled services. Train operators
are shown because operators such as SJ and VY may have different ticket conditions.

Warnings are based only on estimated delays of at least one minute or API flags
for cancelled/partially cancelled departures. General notices, such as overnight
maintenance, are not shown. **Förseningar och inställda avgångar…** is always
available and shows affected departures from search responses, or indicates
that there are no warnings/information needs updating. Tracking warnings are
available through **Visa bevakad resa** and the top `!` entry. Warnings are
limited to the trains being examined and trams that can connect to them.
Cancelled trains in the searched part of the list are shown within 90 minutes
of the requested arrival (or now for upcoming journeys). Cancelled journeys
are retained as warnings but are not recommended; vehicles that have already
departed are omitted. This uses the same journey requests and cache, without
separate disruption requests. Without active journey tracking, the panel
monitors upcoming journeys for the saved route, not a selected arrival time.
Warnings can only cover departures the API actually returns with this information;
cancelled services missing entirely from the response cannot be detected.

Automatic fetching runs every minute **15:00–16:59**, every day, Swedish time.
Outside this window, `🚋` is dimmed; clicking or using `--now` can search manually.
Arrival may be after 17:00. Without active journey tracking, automatic fetching
stops at 17:00. Selected arrival times are not retained between menu openings.

Responses and tokens are stored privately in `~/.cache/i3blocks/vasttrafik/`.
File locks and caching prevent duplicate requests from multiple monitors.
Errors trigger increasing backoff up to one hour; HTTP 429 respects `Retry-After`
when present. Clicking does not bypass backoff. Stale responses are marked
with the last fetch time. `HTTP 401` concerns authentication; also check the
subscription for `403`. `XDG_CONFIG_HOME` and `XDG_CACHE_HOME` are supported.

The “Åk så snart som möjligt” search from Kaptensgatan to Trollhättan looks for
one feasible journey per station and stops as soon as it finds one. If the first
connection works, both stations require four journey requests: two train searches
and two tram searches. Failed connections trigger checks of at most three trains
per station and two tram pages per train: at most 14 requests in total.
Four requests per minute for two hours is 480 journey requests before cache
reuse; the maximum is 1680. Automatic background fetching uses this approach too.

The initial arrival-time search also requires four requests if the first
connection works. It can search up to three train pages and try three connections
per station, for at most 18 requests across both stations. Requesting more
alternatives increases the budget by the number of requested journeys; at most
two failed connections beyond the requested number are tried per side of the
arrival time and per station. An empty list therefore does not mean every
possible connection has been examined. Identical subqueries share the cache
during the configured interval. Selecting only Centralen or Gamlestaden searches
that station alone and halves these maximums.

Opening or closing the menu does not fetch new information. Other journey
directions use the standard planner: at most three pages for upcoming journeys
or four for the initial arrival-time search. The page limit grows when more
alternatives are requested. Token requests, stop lookups and manual searches
are additional. Set `interval_seconds` to `120` in the private configuration
to halve traffic. The minimum interval is 60 seconds per search; a new arrival
time has its own cache. No numerical quota was listed in the portal's public
API information when checked on 2026-10-06. Check the application's subscription
terms in the portal.

Requests have been checked against
[Västtrafik's OpenAPI schema](https://developer.vasttrafik.se/api/apis/13/v4/swagger),
[REST documentation](https://github.com/vasttrafik/api-pr-docs/blob/main/docs/REST.md)
and real journey responses. The `viaGid` parameter returned HTTP 400 during
verification, so outbound journeys from Kaptensgatan are matched separately
through each station; other routes use complete suggestions from the planner.
Tests: `python3 -m unittest discover -s tests -v`.

The application launcher entry is `i3/vasttrafik.desktop`; install it in
`~/.local/share/applications/` to open the same menu from Rofi.

## Browsers

Firefox is used for the machine interface and assigned to WS4 by i3. The rule
also applies to “Fix app workspaces” in the system menu. Regular Chrome windows
are assigned to WS1.

Chrome is the default browser for links from other applications. On a new installation:

```sh
xdg-settings set default-web-browser google-chrome.desktop
xdg-mime default google-chrome.desktop x-scheme-handler/http x-scheme-handler/https text/html application/xhtml+xml
```

Links and new tabs inside Firefox still open in Firefox.

- `Mod+Ctrl+F`: open the copied URL from the clipboard in a new Firefox tab.
- `Mod+Ctrl+Shift+F`: the same action.

Copy a full address starting with `http://`, `https://` or `file://`, such as
`http://localhost:3000` or `file:///tmp/mockup.html`. Local file links are supported
to open HTML mockups directly. For links with different display text, use the
browser's “Copy link address” action, then the shortcut. Text under the mouse
pointer is not read. `scripts/open-in-firefox.py` shows a Rofi message for invalid text.

## External touchscreen

i3 starts `scripts/map-touchscreen.py`, which maps `ILITEK ILITEK-TP` to the
touch display using its EDID identity instead of a fixed connector name.
The script checks every two seconds and adjusts the touch area after reconnecting,
resolution changes, repositioning or rotation. It uses Python 3, `xinput` and
`xrandr`, and runs at most one instance even when i3 is restarted.

When the display is inactive, touch input is disabled; it is enabled again when
the display returns. Replacing the touchscreen requires updating `DEVICE` and
`DISPLAY_ID` in the script. If multiple displays share the same identity, touch
input is disabled to avoid mapping touches to the wrong display.

Tests: `python3 -m unittest discover -s tests -p 'test_touchscreen.py' -v`.

## Settings to adjust on the next computer

- i3 starts `scripts/lid-suspend-delay.py`: closing the lid suspends the computer
  after fifteen minutes. Opening the lid or docking cancels the countdown.
  Existing locking before suspend and separate idle locking still apply.
  If the script exits, systemd resumes its normal lid handling.
- `i3/config` uses input ID `9` for natural scrolling. This ID is machine-specific.
- “Office monitors” uses `scripts/office-monitors.sh` for four screens with fixed
  connector names. The older three-screen office layout and the home layout
  are also kept in `scripts/`. Adjust these for your hardware. “Single monitor”
  and “Auto-detect monitors” use connected displays dynamically.
- The project picker expects projects under `~/code` and a particular path structure.
- `scripts/lockscreen.sh` references `~/.config/i3/lock.png`, which is missing
  from the current configuration. Add an image or adjust the script before
  using this shortcut. i3's separate lock before suspend uses i3lock directly.
- Git configuration is not included. Set a personal identity or noreply address
  locally in the repository before the first commit; commit metadata also becomes public.
- Chrome app rules in i3 may require reinstalling the corresponding web apps.

## Temporarily move a workspace to the centre monitor

`Super+Ctrl+Arrow` (or `h/j/k/l`) moves the focused workspace to another
monitor and places the pointer in the previously focused window, keeping
keyboard and mouse focus together. This uses `scripts/move-workspace.py`
and `xdotool`.

Press `Super+C`, release the keys, then select `F1`–`F10`. Selecting the same
workspace again moves it back and shows the centre monitor's previous workspace
if it still exists. `Escape` cancels selection. One workspace is moved at a time;
selecting another restores the previous one before bringing the next one over.
The workspace must already be open.

`scripts/center-workspace.py` reads the current monitor layout from i3 each time:

- Three active monitors: the middle one from left to right.
- Two monitors, including one built-in (`eDP`, `LVDS` or `DSI`): the external monitor.
- One monitor: that monitor.
- Other setups: the focused monitor.

Restoration state is stored in `XDG_RUNTIME_DIR`, separately for each i3 session.
If the monitor layout changes, the workspace closes or it is moved manually,
the old placement is no longer used. The next selection uses the current setup.
