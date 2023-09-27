# Les Dépôts

L'organisation de notre base de code repose sur la division entre le frontend,
le backend, et l'infrastructure.

Pour `git`, un dépôt est une unité qui contient l'ensemble de l'historique d'une
base de code. Il est possible pour un dépôt de faire référence à un autre via un
« submodule ».

Pour l'hosting, nous nous reposons sur le service GitHub, qui permet de
collaborer sur des des dépôts `git`. Nous avons une
[organisation](https://github.com/InsaLan) dédiées à tout le code de
l'association.

## Les Trois Dépôts

 - [**InsaLan/backend-insalan.fr**](https://github.com/InsaLan/backend-insalan.fr)
     est le dépôt qui
     contient le backend, c'est à dire la grosse pièce à laquelle nous nous
     intéressons dans ce manuel
 - [**InsaLan/frontend-insalan.fr**](https://github.com/InsaLan/frontend-insalan.fr)
     est le dépôt du code du frontend
 - [**InsaLan/infra-insalan.fr**](https://github.com/InsaLan/infra-insalan.fr)
     est le dépôt qui contient les descriptions de déploiement via Docker
     Compose, et des références vers les deux autres dépôts (pour pouvoir tout
     déployer d'un seul coup)

L'idée principale est de pouvoir diviser les besoins de développement selon le
domaine: frontend, backend, ou tout le système qui tourne autour pour déployer.

Globalement, nous allons nous soucier du backend et de l'infra. Le frontend
restera principalement nébuleux, mais il est utile de savoir qu'il est là et
comment il fonctionne, dans les grandes lignes.

<!--
vim: set tw=80 spell spelllang=fr:
-->
