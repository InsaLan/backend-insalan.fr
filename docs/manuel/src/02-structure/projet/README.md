# Projet

Le projet est l'unité la plus grande de Django. C'est ce qui correspond à la
taille d'une application globale.

## La Commande Django Admin

Un projet est géré via la ligne de commande en utilisant soit la commande
`django-admin` fournie par les paquets Python de Django en ayant fourni le
chemin du module de configuration via la variable d'environnement
`DJANGO_SETTINGS_MODULE`, soit le script `manage.py` qui est fourni à
l'intérieur du projet. Les deux solutions sont strictement équivalentes.

Les commandes disponibles via la commande Django Admin servent par exemple:
 - `compilemessages`/`makemessages`: À faire de la
     [traduction](../../03-existant/traductions.md)
 - `makemigrations`/`migrate`: À gérer les [migrations](../migrations.md) des
     schemas de la base de donnée
 - `sendtestemail`: À vérifier les [paramètres d'email](./configuration.md#Email)
 - `createsuperuser`: À créer un⋅e superutilisateur⋅ice qui a tous les droits
     sur les données
 - `runserver`: À lancer le serveur de développement localement

Et ainsi de suite.

**Important:** Si la commande `manage.py` ne peut pas être lancée, il faut
s'assurer d'avoir bien sourcé les fichiers qui permettent d'entrer dans
l'environnement de développement virtuel Python. Sans cela, Django et les autres
dépendances du projet ne sont pas forcément bien installés, ou pas du tout.

## Anatomie du Projet

Notre projet Django est situé dans le dossier `insalan` du dépôt de backend. À
la racine du dépôt, on trouve le script `manage.py`, la documentation, et les
[traductions](../../03-existant/traductions.md). Dans le dossier `insalan`, on
trouve le dossier des migrations, les modules, la configuration, la liste des
endpoints d'API, et les scripts de WSGI.

Comme ceci:
```
backend
+ insalan/
|   + migrations/
|   + <module1>/
|   + <module2>/
|   + …
|   + asgi.py
|   + wsgi.py
|   + settings.py
|   + urls.py
+ locales/
+ docs/
+ README.md
+ manage.py
```
<!--
vim: set tw=80 spell spelllang=fr:
-->
