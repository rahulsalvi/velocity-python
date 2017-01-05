# velocity

Powerline-based theme elements for ZSH and tmux

## Getting Started

### Prerequisities

* python 3
* a font with powerline characters

### Installing

1. Clone the repository:
    ```
    git clone https://github.com/rahulsalvi/velocity.git "${VELOCITY_DIR:-$HOME}/.velocity"
    ```

2. Add the following line to your .zshrc:
    ```
    [ -f "${VELOCITY_DIR:-$HOME}/.velocity/velocity.zsh" ] && source "${VELOCITY_DIR:-$HOME}/.velocity/velocity.zsh"
    ```

3. Add the following line to your .tmux.conf:
    ```
    source-file $HOME/.velocity/velocity-tmux.conf
    ```
    Note: replace $HOME with $VELOCITY_DIR as necessary

## Configuration

The following environment variables can be used to configure the theme:

```VELOCITY_DIR``` - Set this to the location to where you cloned the project

## Authors

* **Rahul Salvi** - [rahulsalvi](https://github.com/rahulsalvi)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
