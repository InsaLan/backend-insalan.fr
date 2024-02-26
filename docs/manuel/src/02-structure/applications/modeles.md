# Modèles

Les modèles sont des classes Python qui décrivent la structure des données que
l'on souhaite stocker dans la base de données. Ils sont utilisés par Django pour
créer les tables dans la base de données, et pour valider les données que l'on
souhaite y stocker.

## Créer un Modèle

Pour créer un modèle, il suffit de créer une classe Python qui hérite de la
classe `django.db.models.Model`. Par exemple, pour créer un modèle de produit,
on pourrait écrire:

```python
from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=5, decimal_places=2)
    description = models.TextField()

    def Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")

```

Vous avez peut être remarqué que l'on utilise des classes `CharField`,
`DecimalField` et `TextField` pour décrire les [champs](./modeles-champs.md) de
notre modèle.

Nous avons aussi déclaré une classe `Meta` qui permet de décrire des options
pour le modèle. Les [Métadonnées](./modeles-meta.md) sont des options qui ne
sont pas des champs, mais qui décrivent le modèle en lui-même.