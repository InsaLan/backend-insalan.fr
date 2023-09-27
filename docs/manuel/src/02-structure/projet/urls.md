# URLs

Il faut pouvoir décrire la répartition des URLs Django dans le projet. Cela est
fait dans le fichier `insalan/urls.py`. Il y a généralement deux façons de
regrouper les définitions des URLs:
 - une description détaillée dans un seul fichier
 - avoir un fichier d'URL par module, puis les regrouper en une seul en haut du projet

Nous avons opté pour la deuxième solution. Par conséquent, chaque module a une
[description interne de ses URLs](../applications/endpoints.md).

Les URLs sont ensuite rassemblées sous le préfixe qui correspond au module comme
suit:
```python
urlpatterns = [
    # ...
    path("v1/partners/", include("insalan.partners.urls")),
    path("v1/tournament/", include("insalan.tournament.urls")),
    # ...
]
```

<!--
vim: set spell spelllang=fr tw=80:
-->
