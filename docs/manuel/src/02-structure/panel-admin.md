# Panel Admin

Le panel admin est une interface web qui permet de gérer les données de
l'application. C'est notre saint Graal pour gérer les données de l'application.
C'est un outil très puissant, et très complet, qui permet de gérer les données
de l'application sans avoir à écrire une seule ligne de code.

Le fonctionnement par défaut du panel admin est très simple mais si jamais vous
avez le malheur de vouloir le personnaliser, vous allez vite vous rendre compte
que c'est un outil très complexe. Rien n'est impossible, mais il faut être prêt
à mettre les mains dans le cambouis juste pour ajouter un bouton sur une page.

![Panel admin](https://airplane.ghost.io/content/images/2022/06/5.-Categories--Right-Plural--1.png)

## Accéder au Panel Admin

Pour accéder au panel admin, il suffit de se rendre à l'adresse
[`/admin`](https://api.insalan.fr/v1/admin) de l'application. Vous serez alors
redirigé vers une page de connexion. Il suffit de se connecter avec un compte
administrateur pour accéder à l'interface.

/!\ Tout les membres de l'association sont sensés avoir un compte
administrateur, mais si jamais vous n'avez pas les droits, vous pouvez demander
à un membre du staff de vous les donner. /!\

## Gestion des droits

Comme vous pouvez l'imaginer, le panel admin permet aussi de gérer les droits
des utilisateurs. Il est possible de créer des groupes d'utilisateurs, et de
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

## Thème

La panel admin utilise le thème [Unfold](https://unfoldadmin.com/) pour être plus beau (et un peu plus en accord avec le reste du site). On y a apporté quelques customisations, que vous pouvez trouver dans le dictionnaire `UNFOLD` dans `insalan/settings.py`.

Implémenter ce thème ne se fait pas en un clic, surtout à cause du fait qu'il n'a pas de stubs Python, ce qui fait que `mypy` ne peut pas analyser les types de ses objets. Il faut donc manuellement ignorer toutes ces erreurs avec des `# type: ignore` saupoudrés un peu partout dans les fichiers `admin.py`.

Pour plus de détails sur comment implémenter le thème dans un projet existant, voyez [la doc](https://unfoldadmin.com/docs/installation/quickstart/). Il y a des cas spéciaux pour certains modules et certains types de panneaux Django.