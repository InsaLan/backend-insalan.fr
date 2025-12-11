# Panel Admin

Le panel admin est une interface web qui permet de gérer les données de
l'application. C'est notre saint Graal pour gérer les données de l'application.
C'est un outil très puissant, et très complet, qui permet de gérer les données
de l'application sans avoir à écrire une seule ligne de code.

Le fonctionnement par défaut du panel admin est très simple mais si jamais vous
avez le malheur de vouloir le personnaliser, vous allez vite vous rendre compte
que c'est un outil très complexe. Rien n'est impossible, mais il faut être prêt·e
à mettre les mains dans le cambouis juste pour ajouter un bouton sur une page.

![Panel admin](https://airplane.ghost.io/content/images/2022/06/5.-Categories--Right-Plural--1.png)

## Accéder au panel admin

Pour accéder au panel admin, il suffit de se rendre à l'adresse
[`/admin`](https://api.insalan.fr/v1/admin) de l'application. Vous serez alors
redirigé·e vers une page de connexion. Il suffit de se connecter avec un compte
administrateur·rice pour accéder à l'interface.

/!\ Toustes les membres de l'association sont censé·e·s avoir un compte
administrateur·rice, mais si jamais vous n'avez pas les droits, vous pouvez demander
à un·e membre du staff de vous les donner. /!\

## Gestion des droits

Comme vous pouvez l'imaginer, le panel admin permet aussi de gérer les droits
des utilisateur·rice·s. Il est possible de créer des groupes d'utilisateur·rice·s, et de
donner des droits à ces groupes. Par exemple, on peut créer un groupe `Equipe
tournois` qui n'a accès qu'à la gestion des tournois. Facile, non ?

## Personnalisation

On ne va pas rentrer dans des détails compliqués, la plupart du temps vous
n'aurez pas besoin de plus que de rajouter un
[modèle](./applications/modeles.md) dans le panel admin. Pour cela, il suffit de
créer un fichier `admin.py` dans le dossier de l'application, et d'ajouter les
lignes suivantes:

```python
from django.contrib import admin

from .models import MyModel

class MyAdmin(admin.ModelAdmin):
    """Admin handler for MyModel"""

    list_display = ("id", "name", ...)
    search_fields = ["id", "name", ...]


admin.site.register(MyModel, MyAdmin)
```

Dans cet exemple, `MyModel` est le modèle que l'on souhaite ajouter au panel
admin. On crée une classe `MyAdmin` qui hérite de `admin.ModelAdmin`, et on
définit les champs `list_display` (champs à afficher) et `search_fields` (champs
de recherche) pour personnaliser l'affichage du modèle dans le panel admin.
