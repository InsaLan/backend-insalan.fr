# La pile logicielle

On appelle **pile logicielle** l'ensemble des logiciels déployés qui permettent de
déployer un service.

Dans le domaine du web, la pile logicielle comprend généralement 3 composantes de
base:
 - Le serveur web
 - Le backend
 - La base de données (ou les bases de données)

Mais où est le frontend? Pas de panique. Le frontend est en realité une
combinaison de code HTML, CSS et JavaScript qui est servi par le serveur web,
auquel le navigateur se connecte.

Toute la pile est déployée sur le ou les serveurs de production. Typiquement,
l'avantage d'avoir ces composantes séparées est qu'elles peuvent se situer sur des
serveurs différents, ce qui permet de passer à l'échelle (augmenter le nombre de
serveurs pour servir plus de monde), ou de changer des serveurs si besoin sans
rien montrer aux utilisateur⋅rice·s.

L'InsaLan a un VPS, donc nous faisons avec les moyens du bord.

## Nos technologies

Nous avons choisi d'utiliser les technologies suivantes pour les différentes
composantes de notre pile logicielle:

 - [Nginx](https://www.nginx.com/) est notre serveur web. Il a été choisi car il
     est relativement moderne, fonctionnel, et qu'il est déjà déployé sur le VPS
     de l'InsaLan
 - [Django Rest Framework](https://www.django-rest-framework.org/) est une
     extension du *framework* [Django](https://www.djangoproject.com/) qui
     permet d'écrire des sites web en langage [Python](https://www.python.org/).
     L'avantage de DRF est qu'il permet de n'écrire *que* le backend, et les
     morceaux qui permettent l'interaction avec le frontend. L'avantage de
     Python est que c'est un langage facile à prendre en main et souvent déjà
     connu des gens qui arrivent dans l'équipe de développement.
 - [PostgreSQL](https://www.postgresql.org/) est un système de gestion de base
     de données (SGBD) qui permet de gérer un ensemble de bases de données
     relationnelles utilisant le langage PostgreSQL. C'est notre choix de base
     de données relationnelle pour les données persistantes représentées sous
     forme d'[objets](../02-structure/applications/modeles.md).
 - [MongoDB](https://www.mongodb.com/) est notre base de données non
     relationnelle, qui gère l'entièreté des données persistantes de type
     documents (par exemple les textes à afficher sur le site).

## Autres technologies hors de la pile

On notera aussi que toute notre pile est déployée via
[Docker](https://www.docker.com/), qui est un système de conteneurisation, c'est-à-dire qu'il crée des environnements isolés sur le système dans lequel les
programmes s'exécutent, permettant d'avoir une organisation reproductible d'une
machine à l'autre d'une pile logicielle. Nous organisons la pile dans un [Docker
compose](https://docs.docker.com/compose/), qui est une méthode de description
de conteneurs Docker qui permet ensuite de créer tout un ensemble de conteneurs,
et les orchestrer d'une seule commande et tous ensemble.

Tous ces détails sont expliqués plus en profondeur dans la partie sur le
[déploiement](../01-deployer).

Enfin, nous utilisons les *environnements virtuels* de Python, qui sont une
façon d'installer des bibliothèques pour le langage dans un environnement local
dédié à notre projet, sans polluer le système global.

<!--
vim: set spell spelllang=fr tw=80:
-->
