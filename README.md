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
  brightnessctl, xset, setxkbmap, xinput, xrandr and Dunst (`dunstctl`).
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
- The home profile in `scripts/home-three-monitors.sh` uses fixed connector
  names. Adjust these for your hardware. “Single monitor” and
  “Auto-detect monitors” use connected displays dynamically.
- The project picker expects projects under `~/code` and a particular path structure.
- `scripts/lockscreen.sh` references `~/.config/i3/lock.png`, which is missing
  from the current configuration. Add an image or adjust the script before
  using this shortcut. i3's separate lock before suspend uses i3lock directly.
- Git configuration is not included. Set a personal identity or noreply address
  locally in the repository before the first commit; commit metadata also becomes public.
- Chrome app rules in i3 may require reinstalling the corresponding web apps.

## Temporarily move a workspace to the centre monitor

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
