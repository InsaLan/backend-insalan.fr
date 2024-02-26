# Media

Vous avez compris les [statiques](./statiques.md) ? Bah c'est pareil pour les
médias, mais avec un twist. Les médias sont des fichiers qui peuvent être
uploadés dynamiquement, et qui ne sont pas utilisés par le code de
l'application. Par exemple, les images de profil des utilisateurs, ou les logos
des tournois.

Django gère les médias de la même manière que les statiques, mais avec une
configuration différente. Les médias sont stockés dans un dossier spécifique, et
sont servis par un serveur de fichiers statiques. C'est un peu plus compliqué à
mettre en place, mais une fois que c'est fait, c'est transparent pour le code de
l'application.

## Paramétrage

Le paramétrage des médias se fait dans le fichier `settings.py` du projet
Django. On y trouve plusieurs variables qui permettent de configurer le serveur
pour servir les médias.

| Variable | Utilisation |
|-----------------|-------------|
| `MEDIA_ROOT` | Chemin vers le dossier où sont placés les médias |
| `MEDIA_URL` | URL à laquelle correspond le dossier des médias |

La variable `MEDIA_ROOT` est le chemin vers le dossier où sont placés les
médias. C'est le dossier qui est servi par le serveur web pour servir les
médias. Typiquement, on le place dans un dossier `media` à la racine du projet.

La variable `MEDIA_URL` est l'URL à laquelle exposer les médias. Il y a donc une
correspondance entre `MEDIA_URL/<fichier>` et le fichier `MEDIA_ROOT/<fichier>`.

Franchement, c'est tout. C'est pas plus compliqué que ça.