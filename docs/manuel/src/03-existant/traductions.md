# Traductions

L'application du backend est traduite en deux langages: français et anglais.
Les traductions permettent d'avoir un affichage en fonction de la lange définie
dans le navigateur de la personne qui consulte les pages.

Les traductions concernent principalement les messages d'erreur, ainsi que les
descriptions des modèles, champs, et structures dans le panel d'admin de Django.

## Conventions

La convention actuelle est que toutes les chaînes de caractères humainement
lisibles doivent être **en Français** de base. Par habitude, les premières
chaînes de caractère ont été écrites selon une convention de français inclusif.

La traduction est ensuite effectuée mécaniquement par Django, qui utilise les
langues connues pour modifier et re-formater les chaînes traduites.

## Traduction dans le code

Pour pouvoir traduire, le code source du backend doit prendre en compte la
traduction.

### Boilerplate global

Il faut d'abord rajouter du code dans la configuration du site:
1. Le `LocaleMiddleware` doit être chargé
2. La langue par défaut doit être indiquée
3. Il faut indiquer la liste des langues

On aura donc dans `insalan/settings.py`:
```python
from django.utils.translation import gettext_lazy as _

MIDDLEWARE = [
    # ...
    "django.middleware.locale.LocaleMiddleware",
    # ...
]

LANGUAGE_CODE = 'fr'
LOCALE_PATH = 'locale'
USE_I18N = True
LANGUAGES = [
    ("en", _("Anglais")),
    ("fr", _("Français")),
]
```

### Modifications locales

Ensuite, dans le code source, il faut utiliser une méthode de traduction
(typiquement `gettext_lazy`), puis l'appliquer aux chaînes de caractères.

Pour pouvoir rajouter le maximum de chaînes traduisibles, on ajoutera les
classes `Meta` et des champs `verbose_name` aux champs d'un modèle.

```python
class Game(models.Model):
    """A Game"""
    class Meta:
        """Meta Options"""
        verbose_name = _("Jeu")
        verbose_name_plural = _("Jeux")

        name = models.CharField(
            verbose_name = _("Nom du jeu"),
            validators = [MinLengthValidator(2)],
            max_length = 40,
            null = False,
        )
        # ...
```

## Écrire les traductions

Il faut ensuite balayer le code existant dans le dossier `insalan` pour chercher
toutes les chaînes marquées comme traduisibles mais sans traduction. On
utilisera la commande `makemessages` de `django-admin`/`manage.py`, qui créera
au passage le fichier de locale si il n'existe pas.

Dans ce cas, créons ou mettons à jour le fichier pour la locale 'en' (Anglais):
```shell
./manage.py makemessages -l en -i 'env/*'
```

On ignore (`-i`) le dossier `env` car il contient plein de code python des
librairies utilisées par le projet, et nous ne voulons pas les traduire.

### Les fichiers PO

Comme nous avons spécifié que le chemin des locales était `locale` dans
`settings.py`, la commande `djano-admin` l'a pris en compte pour créer les
fichiers dans ce dossier. Après avoir lancé `makemessages` comme indiqué
ci-dessus, on retrouvera le fichier `locale/en/LC_MESSAGES/django.po`.

Le fichier ressemble à ceci:
```po
# SOME DESCRIPTIVE TITLE.
# Copyright (C) YEAR THE PACKAGE'S COPYRIGHT HOLDER
# This file is distributed under the same license as the PACKAGE package.
# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.
#
#, fuzzy
msgid ""
msgstr ""
"Project-Id-Version: PACKAGE VERSION\n"
"Report-Msgid-Bugs-To: \n"
"POT-Creation-Date: 2023-09-25 15:12+0200\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\n"
"Language-Team: LANGUAGE <LL@li.org>\n"
"Language: \n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\n"

#: <chemin>:<ligne>
msgid "Jeu"
msgstr ""

#: <chemin>:<ligne>
msgid "Jeux"
msgstr ""
```

Le chemin et la ligne indiquée font référence à l'emplacement de la chaîne dans
le code. Ils sont utiles pour avoir une idée du contexte dans lequel la
traduction doit être effectuée.

Ensuite, il suffit juste d'écrire dans les champs `msgstr` la traduction dans la
langue cible. On pourra aussi changer les champs d'information sur la
traduction.

Parfois, il y aura des messages formattés avec des champs, comme `{editor}`,
auquel cas ils seront substitués dans votre traduction comme ils l'étaient dans
la chaîne originale.

### Compiler les traductions

Une fois les traductions écrites, il faut compiler ces traductions vers un
fichier `.mo` utilisable par Django. On fera donc:

```shell
./manage.py compilemessages -i 'env/*'
```

On veillera encore une fois à ignorer les fichiers de `env` (l'environnement
local de travail python).
