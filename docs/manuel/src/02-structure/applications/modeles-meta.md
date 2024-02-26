# Métadonnées

Les métadonnées sont des options qui ne sont pas des champs, mais qui décrivent
le modèle en lui-même. Elles sont déclarées dans une classe `Meta` qui est une
classe interne à la classe du modèle.

Les métadonnées que nous utilisons souvent sont `verbose_name` et
`verbose_name_plural` qui permettent de décrire le nom du modèle en lui-même, et
le nom des instances de ce modèle (en vrai c'est juste pour faire zoli dans
l'interface d'administration).

On peut aussi utiliser les métadonnées pour trier les instances d'un modèle par
défaut, ou pour déclarer des contraintes d'unicité sur plusieurs champs.

La [documentation officielle de
Django](https://docs.djangoproject.com/fr/5.0/ref/models/options/) est très
complète et vous pourrez y trouver toutes les informations nécessaires sur les
métadonnées.