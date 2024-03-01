# Pizza

Vous sentez cette bonne odeur de fromage et de tomate ? C'est le module `pizza`
qui arrive ! Ce module permet de gérer les commandes de pizza pour les
événements de l'association. Il permet de créer des types de pizzas, de les
commander, de les annuler, etc.

## Pizzas

Une pizza, c'est quoi ? Bah pour nous c'est juste un nom, une image, des
ingrédients et des allergènes. C'est pas plus compliqué que ça. Et si vous êtes
pas content, vous pouvez toujours aller manger des crêpes de la team Bouffe.

## Créneaux

Les créneaux (ou `timeslots` en anglais) sont les moments où les pizzas peuvent
être commandées. Ils contiennent des informations sur la date de début de
commande, de fin de commande et de livraison, ainsi que le nombre de pizzas
maximum commandables.

Il est assez important de veiller à ce que les besoins de la team Bouffe soient
bien pris en compte, car ils sont souvent dans le rush pour enregistrer les
commandes et les transmettre à la pizzeria.

## Commandes

Là dessus, je vais pas vous faire un dessin. Une commande, c'est une liste de
pizzas commandées par un utilisateur. Elle contient des informations sur
l'utilisateur, la/les pizza/s commandée/s, le créneau, le nombre de pizzas
commandées, le prix, etc.

## Les exports

L'`export` est un modèle qui n'a que pour but de permettre l'export des
commandes sous forme de fichiers CSV pour la pizzeria.