# Connaissances Prérequises

Avant de plonger la tête la première dans le code du backend, il faut savoir de
quoi on parle.

Ça va aller vite, prenons notre temps, et si quelque chose n'est pas clair,
quelqu'un d'autre saura certainement l'expliquer à nouveau.

## Backend VS Frontend

Dans une infrastructure de site web, un **backend** est la partie du site qui
gère le traitement des données. C'est cette partie là qui contient beaucoup
d'opérations compliquées, et qui interagit avec toutes les parties cachées du
site que l'utilisateur⋅ice n'est pas censé⋅e voir, en principe.

Le backend est typiquement un programme distinct de son pendant, le
**frontend**, qui est lui directement présenté à l'utilisateur⋅ice. C'est ce
programme de frontend qui tourne sur son navigateur, qui lui présente les
données formatées en page web, et cache toutes les interactions avec le backend.

Il n'est pas nécessaire de savoir écrire une page web à la main pour gérer le
backend, mais il faut néanmoins savoir que l'on écrit du code avec lequel le
frontend interagit, et garder cela en tête quand l'on conçoit les interactions.

Parfois on entendra aussi parler de **middleware**, qui, comme leur noms
l'indiquent, sont au milieu de ces interactions. En réalité, ce sont des
composants du backend, mais ils modifient les demandes et retour du/vers le
frontend selon leur travail. Par exemple, un des middlewares déployés sur le
projet du site permet de [traduire](./../03-existant/traductions.md) les chaînes de
caractère à retourner au frontend suivant la configuration des langues du
navigateur.

## Web, API REST

Tout le web repose sur le protocol **HTTP**. Dans l'idée, le navigateur demande
au serveur web d'effectuer une action sur un **chemin** avec un **verbe**, avec
des **headers** associés.

Le site de développement de la fondation Mozilla donne un exemple de la
[structure d'une
URL](https://developer.mozilla.org/en-US/docs/Learn/Common_questions/Web_mechanics/What_is_a_URL):

![Anatomie d'une URL](https://developer.mozilla.org/en-US/docs/Learn/Common_questions/Web_mechanics/What_is_a_URL/mdn-url-all.png)

Nous sommes principalement intéressé⋅es par ce qui se situe après le port ou le
nom de domaine, mais connaître ces concepts aide aussi à comprendre ce qui se
passe quand on développe le backend. En effet, le frontend interagit avec le
backend au travers de requêtes sur des URLs qui forment ce que l'on appelle une
API REST.

### Headers

Les **headers** sont une série de clef-valeurs envoyées par le navigateur au
serveur web pour échanger des métadonnées liées à la requête. C'est ce qui
permet par exemple de passer des cookies, ou maintenir un secret de connexion
qui authentifie auprès du serveur. Cela peut aussi servir à configurer les
préférences de langues, ou indiquer au navigateur combien de temps garder en
cache une ressource au lieu de la redemander au serveur.

### Verbes HTTP

Le protocol HTTP peut utiliser 7 verbes:
 1. `GET`: pour récupérer une ressource (document, entité, etc)
 2. `POST`: pour créer une ressource
 3. `PATCH`: pour mettre à jour des morceaux d'une ressource
 4. `PUT`: pour ajouter des morceaux d'une ressource
 5. `HEAD`: pour envoyer des headers sans ressource
 6. `OPTIONS`: pour voir la liste des verbes utilisables sur un chemin
 7. `DELETE`: pour détruire une ressource

En général, on n'utilisera que les verbes 1 à 4 et 7, avec `PUT` et `PATCH`
utilisés de façon interchangeable.

Dans l'idée, le serveur web interprète le chemin fourni, ainsi que les
paramètres donnés, en conjonction avec le verbe donné par le navigateur, pour
comprendre ce qui est demandé, et agir en conséquence. Si vous demandez
`/api/produits/vin?nom=StEmilion` au serveur web en `GET` ou en `DELETE`, le
serveur ne se comportera pas pareil.

### API REST

Le frontend et le backend communiquent, dans notre cas, via une **API**
(*Application Programming Interface*), que l'on qualifiera d'API **REST**. C'est
un modèle de conception d'API web dans lequel le chemin d'une URL représente une
ressource au niveau du serveur, un objet abstrait qui peut alors être manipulé
via les chemins et les verbes HTTP. Par exemple, on peut utiliser `POST` pour
créer une ressource, `GET` pour voir une ressource ou une liste des ressources
existantes, `PUT`/`PATCH` pour mettre à jour une ressource, et `DELETE` pour la
détruire.

Nous utilisons peu les paramètres d'URL dans notre API, mais certaines API les
utilisent pour passer des arguments optionnels aux requêtes.

## Base de donnée

Le backend enregistre ses données persistantes (c'est-à-dire qui sont maintenues
d'une exécution à l'autre) dans une ou plusieurs **bases de données**. Les bases
de données **relationnelles** sont constituées de tables, qui contiennent des
entrées. Une table associe des clefs avec des valeurs, selon une structure de
champs qui lui est propre, aussi appelé **schema**.

Par exemple, une base de donnée relationnelle pour gérer le stock d'un vendeur
de vins pourrait contenir une table pour les clients, une table pour les
produits, une table pour les transactions effectuées, etc. La table des produits
pourrait associer un numéro d'identifiant (`id`) unique à un produit décrit par
son type (`rouge`, `blanc`, …), son vignoble (un champs de texte), son
millésime (un entier), etc. La table aurait un schema où chaque entrée contient
les champs `(id, type, vignoble, millesime)`.

Les bases de données relationnelles modernes reposent pour beaucoup sur un
standard de langage commun nommé *Structured Query Language*, ou **SQL**.

Une base de donnée **non-relationnelle** associe généralement simplement une
clef à une valeur. Nous les utiliserons principalement pour stocker des grosses
quantités de texte à afficher sur le site. Par opposition aux bases précédentes,
on appelle souvent ces bases de données des bases **NoSQL**.

## Git

Toute notre gestion du code passe par l'utilisation de `git`. C'est un outil
extrêmement puissant, mais qu'il est trop long de décrire. Il existe
heureusement une
[formation](https://git.vulpinecitrus.info/Lymkwi/surviving-git/src/branch/master/build/default/default.pdf)
qui permet de se familiariser avec les commandes de base de `git` et pourquoi
elles fonctionnent comme elles fonctionnes.

L'idée globale cependant: `git` permet de capturer des sauvegardes successives
de notre code, et de les associer à du texte pour expliquer les modifications
effectuées. Ces captures (ou « commits ») peuvent ensuite être partagées et
distribuées à d'autres contributeur⋅ices du projet pour collaborer ensemble.

## Python

Le backend utilise le langage [Python](https://www.python.org/) pour son code.
C'est un langage facile à prendre en main et apprendre.

<!--
vim: set spell spelllang=fr tw=80:
-->
