# Set prompt
setopt PROMPT_SUBST
PROMPT=''

# Draw a new prompt each time
precmd() {
    PROMPT=$(python3 ${VELOCITY_DIR:-$HOME}/.velocity/velocity.py PROMPT)
}

# Redraw prompt on resize
TRAPWINCH() {
    PROMPT=$(python3 ${VELOCITY_DIR:-$HOME}/.velocity/velocity.py PROMPT)
}
