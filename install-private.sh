#!/usr/bin/env bash
set -euo pipefail

repository_directory=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)

if [[ "${1:-}" != "--apply" || $# != 1 ]]; then
    if [[ $# != 0 && "${1:-}" != "--help" ]]; then
        printf 'Unknown argument. Use --apply or --help.\n' >&2
        exit 1
    fi
    cat <<'HELP'
Private Debian 13 installation (amd64). No changes are made without --apply.

Run on the NEW computer, as your regular user:
  bash install-private.sh --apply

Installs packages from install/packages-private.txt, Chrome, Spotify, Docker,
Neovim 0.12.5, Meslo Nerd Font, NVM/Node 24, pnpm and tree-sitter-cli.
Copies private dotfiles and backs up existing configuration.
Installs TPM and conventional-commits dependencies. Plugin activation and
personal sign-ins are covered in install/README.md.

Preview configuration destinations only:
  python3 install/private-config.py
HELP
    exit 0
fi

if [[ $EUID == 0 ]]; then
    printf 'Run as your regular user, without sudo before the script.\n' >&2
    exit 1
fi

source /etc/os-release
if [[ "$ID" != debian || "$VERSION_ID" != 13 || "$(dpkg --print-architecture)" != amd64 ]]; then
    printf 'This script requires Debian 13 on amd64.\n' >&2
    exit 1
fi

temporary_directory=$(mktemp -d)
trap 'rm -rf -- "$temporary_directory"' EXIT
trap 'printf "Installation stopped at line %s. Fix the error and rerun; see install/README.md.\n" "$LINENO" >&2' ERR

mapfile -t packages < <(sed '/^[[:space:]]*#/d; /^[[:space:]]*$/d' "$repository_directory/install/packages-private.txt")
sudo apt-get update
sudo apt-get install -y "${packages[@]}"

# Download completely before running an installer or changing its destination.
curl -fL --retry 3 https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -o "$temporary_directory/chrome.deb"
sudo apt-get install -y "$temporary_directory/chrome.deb"

if ! dpkg-query -W -f='${Status}' spotify-client 2>/dev/null | grep -q 'install ok installed'; then
    curl -fL --retry 3 https://download.spotify.com/debian/pubkey_5384CE82BA52C83A.asc -o "$temporary_directory/spotify.asc"
    sudo install -Dm644 "$temporary_directory/spotify.asc" /etc/apt/keyrings/spotify-private.asc
    printf '%s\n' 'deb [signed-by=/etc/apt/keyrings/spotify-private.asc] https://repository.spotify.com stable non-free' |
        sudo tee /etc/apt/sources.list.d/spotify-private.list >/dev/null
    sudo apt-get update
    sudo apt-get install -y spotify-client
fi

if ! dpkg-query -W -f='${Status}' docker-ce 2>/dev/null | grep -q 'install ok installed'; then
    curl -fL --retry 3 https://download.docker.com/linux/debian/gpg -o "$temporary_directory/docker.asc"
    sudo install -Dm644 "$temporary_directory/docker.asc" /etc/apt/keyrings/docker-private.asc
    printf '%s\n' 'deb [arch=amd64 signed-by=/etc/apt/keyrings/docker-private.asc] https://download.docker.com/linux/debian trixie stable' |
        sudo tee /etc/apt/sources.list.d/docker-private.list >/dev/null
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi

neovim_version=0.12.5
neovim_directory="$HOME/.local/opt/nvim-$neovim_version"
mkdir -p "$HOME/.local/bin" "$HOME/.local/opt" "$HOME/.local/share/fonts/Meslo"
export PATH="$HOME/.local/bin:$PATH"

if [[ ! -d "$neovim_directory" ]]; then
    curl -fL --retry 3 "https://github.com/neovim/neovim/releases/download/v$neovim_version/nvim-linux-x86_64.tar.gz" -o "$temporary_directory/nvim.tar.gz"
    tar -xzf "$temporary_directory/nvim.tar.gz" -C "$temporary_directory"
    mv "$temporary_directory/nvim-linux-x86_64" "$neovim_directory"
fi
if [[ -e "$HOME/.local/bin/nvim" || -L "$HOME/.local/bin/nvim" ]]; then
    if [[ "$(readlink "$HOME/.local/bin/nvim" || true)" != "$neovim_directory/bin/nvim" ]]; then
        mv "$HOME/.local/bin/nvim" "$HOME/.local/bin/nvim.backup-$(date +%s%N)"
    fi
fi
ln -sfn "$neovim_directory/bin/nvim" "$HOME/.local/bin/nvim"

curl -fL --retry 3 https://github.com/ryanoasis/nerd-fonts/releases/download/v3.4.0/Meslo.zip -o "$temporary_directory/Meslo.zip"
unzip -oq "$temporary_directory/Meslo.zip" -d "$HOME/.local/share/fonts/Meslo"
fc-cache -f

export NVM_DIR="$HOME/.nvm"
if [[ ! -s "$NVM_DIR/nvm.sh" ]]; then
    curl -fL --retry 3 https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh -o "$temporary_directory/nvm-install.sh"
    PROFILE=/dev/null bash "$temporary_directory/nvm-install.sh"
fi
# NVM is sourced with nounset disabled, as recommended for shell integrations.
set +u
source "$NVM_DIR/nvm.sh"
nvm install 24
nvm alias default 24
set -u
npm install -g pnpm@10
curl -fL --retry 3 https://github.com/tree-sitter/tree-sitter/releases/download/v0.27.0/tree-sitter-linux-x64.gz -o "$temporary_directory/tree-sitter.gz"
gzip -dc "$temporary_directory/tree-sitter.gz" > "$temporary_directory/tree-sitter"
chmod +x "$temporary_directory/tree-sitter"
if [[ -e "$HOME/.local/bin/tree-sitter" || -L "$HOME/.local/bin/tree-sitter" ]]; then
    mv "$HOME/.local/bin/tree-sitter" "$HOME/.local/bin/tree-sitter.backup-$(date +%s%N)"
fi
mv "$temporary_directory/tree-sitter" "$HOME/.local/bin/tree-sitter"

python3 "$repository_directory/install/private-config.py" --apply
pnpm --dir "$HOME/.config/scripts/conventional-commits" install --frozen-lockfile

if [[ ! -d "$HOME/.tmux/plugins/tpm" ]]; then
    git clone https://github.com/tmux-plugins/tpm "$HOME/.tmux/plugins/tpm"
fi

cat <<'DONE'

Applications and private configuration are installed.
1. Log out and select i3 on the login screen.
2. Start tmux and press Ctrl-a, then Shift-i to install plugins.
3. Open nvim, run :Lazy restore and then :checkhealth.
4. Sign in to Chrome/Spotify with your personal accounts.
See install/README.md for recovery, optional setup and known differences.
DONE
