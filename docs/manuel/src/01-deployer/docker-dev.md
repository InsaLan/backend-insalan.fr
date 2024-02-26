# Docker de Développement

Le dépôt d'[infra](https://github.com/InsaLan/infra-insalan.fr) contient des
recettes de Docker compose pour pouvoir déployer une pile en local.

Il faudra que l'utilisateur qui lance ces commandes soit dans le groupe `docker`
du système, pour pouvoir accéder au démon Docker.

## Lancer le Compose Dev

En allant dans le dossier de l'infra, après checkout des modules, lancer:
```shell
docker compose -f docker-compose-beta.yml build
```

Cette commande construit nos images docker personnalisées avec le code du front,
du back, et les paquets nécessaires pour les lancer. Ensuite, on lance ces
dockers:

```shell
docker compose -f docker-compose-beta.yml up -d
```

Cette commande va lancer 5 choses:
 - Le nginx interne
 - Le backend en mode développement, ce qui veut dire qu'il rafraichira le code
     du dossier `backend` dans le docker dès qu'il détecte un changement
 - Le frontend en mode développement, ce qui causera un rafraichissement
     identique en cas de modification du code dans `frontend`
 - Une base de données PostgreSQL avec persistance des données
 - Une base de données MongoDB avec persistance des données

Le `-d` spécifie que la sortie standard, qui fournit tous les logs des dockers
lancés, est détachée par défaut de la sortie standard du shell: une fois le
lancement fini, on récupère un prompt au lieu de suivre les logs des dockers
(comportement par défaut).

## Développer

Pour le backend, le code est situé dans `backend`. On pourra gérer ce dossier
comme un dépôt git à part, puisque c'est un submodule du dépôt d'infrastructure.

N'importe quelle modification du code dans le dossier `backend` est répercutée
dans le docker.

Vous n'avez pas besoin d'activer l'environnement de développement si vous
préférez plutôt lancer les commandes de `manage.py` dans le docker, via:
```
docker exec -it -u nobody infra-insalanfr-beta-backend-1 python3 manage.py <command>
```

C'est particulièrement utile pour faire `manage.py test`, par exemple (même si
on préfèrera ne pas utiliser `-u nobody` dans ce cas, et les lancer en tant que
`root` dans le docker, pour avoir les droits d'écriture sur le dossier des
statics).

<!--
vim: set tw=80 spell spelllang=fr:
-->
