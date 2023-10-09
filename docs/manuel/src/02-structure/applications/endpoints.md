# Endpoints

Un endpoint d'application est la combinaison d'une URL pouvant contenir des
paramètres, et une [./vues.md](vue) qui gère le traitement de la requête, avec
potentiellement des paramètres.

## Déclaration dans le module

Chaque module dans notre projet contient un fichier `urls.py`, qui exporte les
endpoints créés par le module, et décrit les potentiels paramètres des requêtes,
et les traitants.

La liste des URLs est appelée `urlpatterns`, et contient des successions
d'appels à la fonction [`path`](https://docs.djangoproject.com/en/4.2/ref/urls/)
pour décrire chaque chemin. On retrouve dans la configuration:
 - Une chaîne de caractères qui décrit le chemin à partir de la racine du module
 - Une vue associée pour effectuer le traitement
 - Un nom qui permet d'effectuer une recherche dans le code

La prise de décision pour traiter une requête consiste à chercher un match exact sur
les URLs proposés.

### Paramètres du path

Il arrive souvent que l'on souhaite transmettre des informations à travers le
chemin de la requête HTTP. Pour dire à Django que l'on souhaite réceptionner ces
parties variables de la requête, on utilise la syntaxe entre chevrons
`<type:nom>` qui décrit les contraintes sur ces paramètres:
 - `<int:user_id>` décrit que l'ont cherche un entier naturel qui sera ensuite
     appelé dans le traitant `user_id`
 - `<int:pk>` indique que l'on cherche un entier qui sera appelé `pk` dans le
     traitant. Les vues par défaut de DRF (`APICreateView`, etc), utilisent `pk`
     comme nom de variable
 - `<str:username>` indique que l'on cherche une chaîne de caractère qui sera
     passée dans la variable `username` au traitant

### Reverse Lookup

Pour ne pas hardcoder d'URLs dans le code, on utilise le nom d'un endpoint pour
le retrouver. Par exemple, si une route est nommée `tournament/details-full`
mais que je décide de changer son chemin exact, je n'aurai pas besoin d'écrire
du code qui vient chercher ce chemin via la fonction
[`reverse`](https://docs.djangoproject.com/en/4.2/ref/urlresolvers/#reverse).

On peut aussi utiliser l'objet retourné par `reverse` pour substituer des
arguments directement dans l'URL:
```python
query_url = reverse("tournament/details-full", args=[tournament_id])
request = self.client.get(query_url)
self.assertEqual(request.status_code, 200)
```

Ici, on a substitué le paramètre `tournament_id` dans la query à
`/v1/tournament/tournament/<int:primary_key>/full`. Si `tournament_id` valait
`2` par exemple, on a lancé notre requête à `/v1/tournament/tournament/2/full`,
le tout sans avoir à écrire le chemin en dur.

## Documentation Via Swagger

L'API est documentée (autant que possible) via un fichier au format
[OpenAPI-compatible](https://www.openapis.org/) que l'on peut ouvrir dans
l'outil [Swagger](https://editor.swagger.io/). Cela permet de voir:
 - l'ensemble des chemins existants classés par catégorie
 - les méthodes disponibles
 - la liste des codes de retour possible et leur signification
 - la forme des payload attendus
 - la forme des payload retournés

<!--
vim: set spell spelllang=fr tw=80:
-->
