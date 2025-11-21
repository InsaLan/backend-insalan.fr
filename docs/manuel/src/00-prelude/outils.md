# Installer les outils

Pour qu'il te soit possible de déployer et travailler sur le backend, il faut
que tous les outils nécessaires soient installés.

Généralement, on recommande l'utilisation de Linux pour le développement (c'est
un choix qui est aussi globalement fait au département INFO), mais il est
possible de faire tourner ce qu'il faut sous Windows, généralement grâce à
*WSL*.

À la fin de cette section, tu devrais avoir tous les outils pour déployer
localement le projet, et travailler dessus.

## Sur Linux

Suivant la distribution utilisée, il faut installer les paquets nécessaires de
base:

Pour Debian:
```shell
apt install git python3 build-essential
```

Pour Arch Linux:
```shell
pacman -S git python binutils
```

## Sur Windows

TODO

## Docker

Pour installer Docker, suivre le [tutoriel](https://docs.docker.com/engine/install/)
qui correspond à la bonne distribution, et le bon OS.

<!--
vim: set spell spelllang=fr tw=80:
-->
