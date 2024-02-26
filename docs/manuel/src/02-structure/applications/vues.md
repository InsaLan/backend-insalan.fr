# Vues

Les vues sont des fonctions Python qui prennent une requête HTTP et renvoient
une réponse HTTP. Elles sont utilisées dans le cadre de l'API REST pour gérer
les requêtes du client.

## Créer une Vue

Malheureusement, il n'existe pas de méthode standard pour créer une vue, car
cela dépend de ce que l'on souhaite faire. Cependant, il existe des classes
prédéfinies dans Django REST Framework qui permettent de gérer les requêtes
courantes.

On retrouve notamment les classes :
- `rest_framework.generics.RetrieveAPIView` pour gérer les requêtes GET sur un
    objet unique
- `rest_framework.generics.ListCreateAPIView` pour gérer les requêtes GET et
  POST sur une liste d'objets
- `rest_framework.generics.RetrieveUpdateDestroyAPIView` pour gérer les requêtes
    GET, PUT, PATCH et DELETE sur un objet unique
- `rest_framework.viewsets.ModelViewSet` pour gérer les requêtes GET, POST, PUT,
    PATCH et DELETE sur une liste d'objets
- ...

Il est aussi possible de créer des vues personnalisées en héritant de la classe
`rest_framework.views.APIView` et en définissant les méthodes `get`, `post`,
`put`, `patch`, `delete`, ...

Par exemple, pour créer une vue qui liste les produits, on pourrait écrire :

```python
from rest_framework import generics, permissions

from .models import Product
from .serializers import ProductSerializer

class ProductList(generics.ListAPIView):
    """
    Get all products
    """
    paginator = None
    serializer_class = ProductSerializer
    queryset = Product.objects.all()
    permission_classes = [permissions.IsAdminUser]
```

Certains paramètres de classe peuvent être définis pour configurer la vue, comme
`paginator` pour spécifier la pagination, `serializer_class` pour définir le
[serializer](./serializers.md) à utiliser, `queryset` pour définir les objets à
renvoyer, et `permission_classes` pour définir les permissions nécessaires pour
accéder à la vue.

Attention, soyez prudents avec les comportements par défaut des vues
prédéfinies, car ils peuvent ne pas correspondre à ce que vous souhaitez faire.
Par exemple, la vue `ListCreateAPIView` permet de créer des objets avec une
requête POST, ce qui peut ne pas être souhaitable dans certains cas.

## Utiliser une Vue

Les vues sont appelées automatiquement par Django REST Framework lorsqu'une
requête correspond à leur URL comme décrit dans le [fichier de configuration des
URLs](./endpoints.md).