alias git='LANG=en_GB git'
alias gst='git status'
alias vim='nvim'
alias ll="ls -all"
alias persist-ssh='eval "$(ssh-agent -s)" && ssh-add ~/.ssh/id_ed25519'
alias fp='bash ~/.config/scripts/fuzzy-select-project.sh'
alias fpn='bash ~/.config/scripts/fuzzy-select-named-project.sh'
alias tks='bash ~/.config/scripts/kill-tmux-session.sh'
alias cc="node ~/.config/scripts/conventional-commits/index.mjs"
alias screen-2='bash ~/.config/scripts/display-two-screens.sh'
alias screen-3='bash ~/.config/scripts/display-three-screens.sh'
jira-my-issues() {
    local answer
    local query='project IS NOT EMPTY AND assignee = currentUser()'

    read -r -p 'Hide completed tickets? [Y/n] ' answer || return

    case "$answer" in
        n|N|no|No|NO) ;;
        *) query+=' AND statusCategory != Done' ;;
    esac

    jira issue list --jql "$query" --columns key,summary,status --no-truncate
}

jira-my-sprint() {
    local answer
    local query='project IS NOT EMPTY AND sprint in openSprints() AND assignee = currentUser()'

    read -r -p 'Hide completed tickets? [Y/n] ' answer || return

    case "$answer" in
        n|N|no|No|NO) ;;
        *) query+=' AND statusCategory != Done' ;;
    esac

    jira issue list --jql "$query" --columns key,summary,status --no-truncate
}
alias gsta='git status --short --ignored --untracked-files=all'
