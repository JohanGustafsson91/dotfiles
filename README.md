# Dotfiles för Debian

Personlig konfiguration, insamlad från Debian 13.6. Program, hemligheter,
plugininstallationer och sessionsdata ingår inte.

## Filer och destinationer

| I repot | Destination |
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

Lazygits konfigurationsfil är för närvarande tom och använder standardinställningar.

## Installation

1. Installera Git och klona repot till `~/code/dotfiles-debian`.
2. Installera programmen nedan.
3. Jämför befintliga konfigurationer med tabellen och säkerhetskopiera dem innan
   du ersätter dem. Debian skapar normalt redan `.bashrc` och `.profile`.
4. Symlänka filerna/mapparna från repot till destinationerna i tabellen.
   Exempel när destinationen inte redan finns:

   ```sh
   mkdir -p ~/.config
   ln -s "$HOME/code/dotfiles-debian/nvim" "$HOME/.config/nvim"
   ```

5. Installera TPM om `~/.tmux/plugins/tpm` saknas:

   ```sh
   git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
   ```

   Starta tmux och tryck `Ctrl-a` följt av `I` för att installera plugins.
6. Starta Neovim och kör `:Lazy restore` för att återställa pluginversionerna från
   `lazy-lock.json`. Mason och Treesitter installerar ytterligare verktyg/parsers;
   nätåtkomst och byggverktyg behövs. Kontrollera `:checkhealth` efter installation.
7. Kör `pnpm install --frozen-lockfile` i
   `~/.config/scripts/conventional-commits` för aliaset `cc`.
8. Skapa lokala hemligheter enligt nedan, anpassa hårdvaruinställningar och
   välj i3 vid inloggning.

På ursprungsdatorn är alla konfigurationer i tabellen symlänkade till repot.
Originalen finns säkerhetskopierade under `~/.local/state/dotfiles-backups/`.
Git-identitet och hemligheter hanteras separat utanför repot.

## Beroenden

Listan bygger på konfigurationerna och är inte en fullständig export av
installerade paket. En installation på en blank dator är ännu inte verifierad.

- Skrivbord: i3 med stöd för gaps, i3blocks och dess standardskript, Alacritty,
  Rofi, Flameshot, dex, xss-lock, i3lock, NetworkManager/nm-applet, pactl,
  brightnessctl, xset, setxkbmap, xinput och xrandr.
- Shell och utveckling: Bash, bash-completion, Git, tmux, fzf, ripgrep,
  Neovim, lazygit, Starship, NVM/Node.js, pnpm och Go.
- Neovim/plugins: C-kompilator och make, Python med stöd för virtuella miljöer,
  unzip, curl, ett X11-urklippsverktyg som xclip samt xmllint.
- Låsskärmsskriptet använder ImageMagicks `import` och `convert`.
- Typsnitt: MesloLGL Nerd Font Propo för Alacritty, JetBrains Mono för i3 och
  JetBrainsMono Nerd Font för Rofi. Installera typsnitten separat och kör `fc-cache -f`.
- i3 har regler för Chrome, Slack och Spotify, och startar Spotify automatiskt.

## Lokala hemligheter

`.bashrc` läser `~/.bash_secrets` om filen finns. Den filen ska ligga utanför
repot och ha rättigheten `600`. Skapa den på en ny dator med:

```sh
(umask 077; touch "$HOME/.bash_secrets")
chmod 600 "$HOME/.bash_secrets"
```

Lägg lokala miljövariabler med hemliga värden där. Kopiera aldrig riktiga
tokenvärden till repot. `.gitignore` utesluter även filer med namnet `.bash_secrets`.
SSH-nycklar installeras separat; aliaset `persist-ssh` förutsätter `~/.ssh/id_ed25519`.

## Saker att anpassa på nästa dator

- `i3/config` använder input-ID `9` för naturlig scrollning. ID:t är maskinberoende.
- `scripts/display-*-screens.sh` innehåller skärmutgångar och upplösningar för
  nuvarande dator.
- `i3/i3blocks.conf` och `bash/.bashrc` innehåller sökvägar med `/home/johan`.
  Projektväljaren förutsätter också projekt under `~/code` och en viss sökvägsstruktur.
- `scripts/lockscreen.sh` hänvisar till `~/.config/i3/lock.png`, som saknas i
  nuvarande konfiguration. Lägg till en bild eller anpassa skriptet innan denna
  genväg används. i3:s separata låsning före vila använder i3lock direkt.
- Git-konfiguration ingår inte. Ange en privat identitet eller en noreply-adress
  lokalt i repot före första commit; även commitmetadata blir offentlig.
- Chrome-appreglerna i i3 kan kräva att motsvarande webbappar installeras igen.
