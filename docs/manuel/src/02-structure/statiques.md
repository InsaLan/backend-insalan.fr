# Statiques

Le backend Django doit souvent servir du contenu dit « statique », c'est à dire
du contenu qui ne changera pas. Cela englobe souvent les images et autres
assets, comme par exemple le logo de l'association.

Certains statiques sont récupérés automatiquement par Django, comme par exemple
les fichiers CSS et JS. D'autres sont à placer dans un dossier dédié à cet
effet.

## Paramétrage

Le paramétrage des statiques se fait dans le fichier `settings.py` du projet
Django. On y trouve plusieurs variables qui permettent de configurer le serveur
pour servir les statiques.

| Variable | Utilisation |
|-----------------|-------------|
| `STATIC_ROOT` | Chemin vers le dossier où sont placés les statiques |
| `STATIC_URL` | URL à laquelle correspond le dossier des statiques |
| `STATICFILES_DIRS` | Liste des dossiers où chercher les statiques |

La variable `STATIC_ROOT` est le chemin vers le dossier où sont placés les
statiques. C'est le dossier qui est servi par le serveur web pour servir les
statiques. Typiquement, on le place dans un dossier `static` à la racine du
projet.

La variable `STATIC_URL` est l'URL à laquelle exposer les statiques. Il y a donc
une correspondance entre `STATIC_URL/<fichier>` et le fichier
`STATIC_ROOT/<fichier>`.

La variable `STATICFILES_DIRS` est une liste de dossiers où chercher les
statiques. Attention, il ne s'agit pas de dossiers qui sont servis par le
serveur web, mais de dossiers où Django va chercher les statiques pour les
copier dans `STATIC_ROOT`. Une erreur courante est de placer le dossier
`STATIC_ROOT` dans un sous-dossier de `STATICFILES_DIRS`. Cela a pour effet de
copier les statiques récursivement dans `STATIC_ROOT` à chaque fois que le
serveur est lancé, ce qui peut vite devenir problématique.