# Serializer

## Introduction

Normalement vous avez lu l'[introduction à l'API
REST](../../00-prelude/prerequis.md#api-rest) avant de lire cette section donc
vous ne devriez pas être perdu. Si ce n'est pas le cas, je vous invite à le
faire avant de continuer.

Les serializers sont des classes qui permettent de transformer des objets Python
en JSON, et vice-versa. Ils sont utilisés dans le cadre de l'API REST pour
transformer les objets des modèles en JSON, et pouvoir les envoyer au client (le
frontend dans notre cas).

## Créer un Serializer

Pour créer un serializer, il suffit de créer une classe Python qui hérite de la
classe `rest_framework.serializers.ModelSerializer`. Par exemple, pour créer un
serializer de produit, on pourrait écrire:

```python
from rest_framework import serializers

from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'description']
```

Vous avez peut être remarqué que l'on utilise une classe `Meta` qui permet de
décrire des options pour le serializer. Les Métadonnées des serializers sont
très similaires à celles des [modèles](./modeles-meta.md), et vous pouvez
retrouver toutes les options possibles dans la [documentation officielle de
Django REST
Framework](https://www.django-rest-framework.org/api-guide/serializers/#serializer).

Il est possible d'avoir un serializer partiel qui ne contient pas tous les
champs du modèle, ce qui peut être pratique pour ne pas envoyer des données
inutiles ou privée au client.

A l'inverse, il est possible de déclarer des champs qui ne sont pas des champs
du modèle. Par exemple, le serializer du modèle Player contient un champ
`password` qui n'est pas un champ du modèle, mais qui est utilisé pour stocker
le mot de passe et le vérifier avec celui de l'équipe lors de la création d'un
joueur via requête POST.

## Utiliser un Serializer

Pour utiliser un serializer, il suffit de l'instancier avec un objet de modèle,
et d'appeler la méthode `data` pour obtenir le JSON correspondant. Par exemple,
pour obtenir le JSON d'un produit, on pourrait écrire:

```python
product = Product.objects.get(id=1)
serializer = ProductSerializer(product)
json = serializer.data
```

Et voilà, vous avez maintenant un JSON qui représente votre produit, et que vous
pouvez envoyer au client. Vous pouvez aussi utiliser un serializer pour
transformer un JSON en objet de modèle, mais nous n'aurons pas besoin de le
faire dans notre projet.