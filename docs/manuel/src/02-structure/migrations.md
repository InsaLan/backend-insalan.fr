# Migrations

Les modèles créés via Django sont formatés automatiquement par la partie ORM
(*Object Relation Mapping*) du framework en *tables* SQL. Les migrations
permettent de suivre les évolutions passées et futures des modèles, et les
répercuter sur la base de donnée relationnelle.

## Kézako SQL?

Il serait beaucoup trop compliqué de refaire un cours entier sur le
fonctionnement de SQL, à la place, on peut partir des approximations suivantes:
 - Django connaît des modèles que nous définissons
 - Ces modèles sont traduits en tables avec un format qui correspond à nos
     champs et leurs contraintes
 - Les tables contiennent des entrées, qui sont les instances de nos objets

## Gérer les migrations

Toutes les migrations sont fractionnées par application, dans un dossier
`./migrations` à la racine de chaque application. Lorsque vous avez effectué des
modifications sur les modèles ou contraintes, et qu'il faut les répercuter sur
la base de donnée, on passe toujours par une génération des migrations via:
```shell
./manage.py makemigrations
```

Suivi de
```shell
./manage.py migrate
```

Cette dernière commande applique les migrations qui sont nouvelles à votre base
de donnée relationnelle.

### Gestion dans le contrôle de version

Étant donnée que les migrations sont liées à un état de la base de donnée à un
instant T, on considère qu'il ne faut pas commit les migrations (sauf celles
appliquées en production). À cause de cela, nous avons une règle dans le
`.gitignore` du backend qui ignore tous les fichiers dans les dossiers
`migrations` qui commencent pas un chiffre.

Cependant, pour que Django puisse continuer de fonctionner, `migrations` doit
être un sous-module de chaque application, **il faut donc conserver le fichier
`__init__.py`**.

### Wipe de base de donnée

Si vous êtes dans un environnement local et que vous repartez de zéro
(destruction de la base de donnée, pour quelconque raison), il est aussi
préférable de détruire les migrations.

Pour ce faire, vous pouvez utiliser la commande suivante à lancer depuis la
racine du backend:
```shell
find -type f -regex './insalan/.*/migrations/[0-9]+_.*.py' -exec rm '{}' \;
```

<!--
vim: set spell spelllang=fr tw=80:
-->
