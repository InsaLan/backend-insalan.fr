# Champs 

Les champs de modèles sont des classes Python qui décrivent les types de données
que l'on souhaite stocker dans la base de données. Ils sont utilisés par Django
pour créer les tables dans la base de données, et pour valider les données que
l'on souhaite y stocker.

Si nous reprenons l'exemple du [modèle de produit](./modeles.md), nous avons
utilisé des classes `CharField`, `DecimalField` et `TextField` pour décrire les
champs de notre modèle.

Il existe de nombreux types de champs, pour plein de types de données
différents. Nous ne les décrirons pas tous ici, mais la [documentation
officielle de
Django](https://docs.djangoproject.com/en/5.0/ref/models/fields/#field-types)
est très complète et vous pourrez y trouver toutes les informations nécessaires.

## Options

Les champs de modèles peuvent aussi prendre des options pour les configurer
comme on le souhaite. Par exemple, on peut spécifier si un champ est unique,
s'il est optionnel, ou s'il a une valeur par défaut.

Ces options peuvent aussi spécifier des contraintes sur les données, comme
précedemment avec `max_length` pour `CharField` ou `max_digits` et
`decimal_places` pour `DecimalField`.

## Champs Spéciaux

Il existe aussi des champs spéciaux qui ne sont pas des types de données de
base, mais qui sont des raccourcis pour des cas d'utilisation courants. On
trouve notamment `ForeignKey` qui est un raccourci pour déclarer une référence à
un autre modèle, et `ManyToManyField` est un raccourci pour déclarer une
référence à un autre modèle avec plusieurs entrées.

## Contraintes

Les contraintes sont des règles qui sont appliquées sur les données stockées
dans la base de données. Certaines options de champs permettent de déclarer des
contraintes, comme expliqué précédemment mais il est aussi possible de déclarer
des contraintes plus complexes, qui portent sur plusieurs champs ou plusieurs
entrées.

Par exemple, on peut déclarer une contrainte qui empêche un joueur de participer
à plusieurs tournois en même temps. Ce genre de contrainte est déclaré dans le
modèle sous forme d'une méthode
[`clean`](https://docs.djangoproject.com/en/5.0/ref/models/fields/#field-types)
qui lève une exception si la contrainte n'est pas respectée.

