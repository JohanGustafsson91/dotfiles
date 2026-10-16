# Set up a new personal Debian computer

Run on **the new computer**, as your regular user. Requires Debian 13 on
Intel/AMD (amd64), internet access, an installed desktop with a display manager,
and access to `sudo`. The script does not change the display manager or drivers.

## Getting started

Install Git first (if sudo is unavailable, use `su -` and grant your account sudo access):

```sh
sudo apt update
sudo apt install git
mkdir -p ~/code
git clone https://github.com/JohanGustafsson91/dotfiles.git ~/code/dotfiles-debian
cd ~/code/dotfiles-debian
bash install-private.sh
bash install-private.sh --apply
```

Cloning assumes the installation commit is available on GitHub. If it only
exists locally, copy the repository including `.git` to the new computer,
or use a Git bundle. On the original computer:

```sh
git bundle create /tmp/dotfiles-debian.bundle --all
```

Transfer the bundle, for example using a USB drive. On the new computer,
replace the clone command with:

```sh
git clone /path/to/dotfiles-debian.bundle ~/code/dotfiles-debian
```

A bundle contains committed Git history, not local configuration secrets
or uncommitted files. HTTPS cloning requires authentication if the repository is private.

## What gets installed

- Debian packages from [packages-private.txt](packages-private.txt): i3, Alacritty,
  Rofi, Flameshot, audio/networking/Bluetooth tools, Firefox, Thunderbird, Git,
  tmux, lazygit, Starship, Go, Python and build tools.
- Chrome from Google, plus Spotify and Docker from their respective signed APT repositories.
- Neovim 0.12.5 and tree-sitter 0.27.0, matching the versions found on the
  original computer, from the projects' GitHub releases. Neovim uses the tar
  archive and therefore does not require FUSE.
- Meslo Nerd Font 3.4.0, NVM 0.40.3, the latest Node 24 release and pnpm 10.
- TPM and dependencies for the `cc` alias.

APT packages, the Node patch version, pnpm and external applications follow
available releases. This recreates the application selection and configuration,
not an exact copy of every binary version. For example, tmux and Starship come
from Debian, while the original computer has newer manual installations.
Line numbers in tmux copy mode require 3.7 and are therefore unavailable in
Debian's 3.5a.

## Private configuration

Configuration is copied from the repository's tracked files, without symlinks,
so the personal computer can be customized without changing the originals.
The older `.config/` directory in the repository is not used; the directories
listed in the main README table are the source.

The private copy excludes Jira functions, Slack rules, fixed
monitor layouts for home, touchscreen mapping and fixed mouse
IDs. The project picker works
with your own projects under `~/code`.

Flameshot's save location is reset to its application default. The lock screen
uses a solid background because the original lock image is missing. The panel
uses the repository's standing/hydration reminder instead of the separately
installed `stand-up-timer`. Bash uses standard `nmtui` instead of the local wrapper.

No projects, VPN profiles, SSH keys, Git identities, browser profiles, tokens,
shell history or tmux sessions are copied. Existing work configuration on a
previously used target computer is not deleted; this is intended for a fresh installation.

## After installation

1. Log out and select **i3** at login.
2. Open a terminal with **Super+Enter**. Start `tmux`, press **Ctrl-a**, then
   **Shift-i** to install TPM plugins.
3. Start `nvim`, run `:Lazy restore`, wait for installations to finish,
   restart Neovim and run `:checkhealth`. Mason and Treesitter download
   language tools and parsers. The installation script does not automatically
   verify completion of these plugin downloads.
4. Open Chrome and Spotify and sign in with personal accounts. Set Chrome
   as the default browser if desired:

   ```sh
   xdg-settings set default-web-browser google-chrome.desktop
   ```

5. Configure monitors through **Ctrl+Esc → Auto-detect monitors** or ARandR.
   Adjust text size in `~/.config/alacritty/alacritty.toml` if needed.
6. Set your personal Git identity with `git config --global user.name 'Your name'`
   and `git config --global user.email 'Your personal address'`.

Slack, OpenVPN/Jira and Freemelt tools are not installed.
ChatGPT and Codex are excluded, including their settings, skills, work
connections and workspace rules. Other Chrome web apps can be installed
separately if needed.
Docker is included as a general development tool and is used with `sudo docker`.
The script does not change your user groups. No images or containers are copied.

## Backups and rerunning

Replaced configuration is moved to
`~/.local/state/dotfiles-backups/<timestamp>/`, preserving relative paths.
Symlinks are preserved too; their target files are not modified.

Rerunning creates a new backup and replaces the installed configuration copies.
Save any personal customizations first. Other user files are unaffected.
An error stops the installation; packages already installed remain in place.
Fix the error and rerun.

To restore i3, for example, move the new `~/.config/i3` aside and move
`.config/i3` back from the desired backup. The same approach applies to
`.bashrc` and the other destinations. Restoring configuration does not uninstall packages.

Preview without installation or network access:

```sh
python3 install/private-config.py
```

Install configuration only (if the applications are already available):

```sh
python3 install/private-config.py --apply
```

## Verification and sources

```sh
bash -n install-private.sh
python3 -m unittest discover -s tests -v
```

Tests cover private filtering, backups, symlinks and repeated installation in
an isolated temporary home directory. A full installation on a fresh Debian
computer still needs to be verified on the target machine.

External installation sources:
[Neovim](https://neovim.io/doc/install/),
[NVM](https://github.com/nvm-sh/nvm),
[Nerd Fonts](https://github.com/ryanoasis/nerd-fonts/releases),
[tree-sitter](https://github.com/tree-sitter/tree-sitter/releases),
[Chrome](https://www.google.com/chrome/),
[Spotify](https://www.spotify.com/us/download/linux/).
