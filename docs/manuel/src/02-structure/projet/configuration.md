# Configuration

La configuration d'un projet Django réside dans `settings.py` à la racine du
projet. Ce fichier contient une **trifouillée** de clefs de configurations qui
sont primordiales pour que Django fonctionne correctement.

## Secrets & Debug

Il est possible de démarrer son application Django en mode de debogage. Dans ce
mode, Django envoie des traces détaillées des erreurs rencontrées, et envoie
dans la console des tonnes d'information en cas de soucis. C'est souvent peu
recommandé dans un vrai déploiement, car cela leak une énorme quantité de
données à quiconque visite le site.

Pour être en mode debug, on met `DEBUG` à `True`. Sinon `False`. La variable
d'environnement `DEV` est lue pour contrôler cela automatiquement (`0` pour
`False`, `1` sinon).

Pour pouvoir chiffrer certaines données de façon consistante et reproductible,
Django a besoin d'un *secret*, c'est à dire d'une longue chaîne de caractère
aléatoire unique et connue seulement de la personne qui déploie le site en
production. Elle est mise dans `DJANGO_KEY`, et piochée dans la variable
d'environnement `DJANGO_SECRET`.

## Allowed Hosts, URLs, CSRF et CORS

Le web est un système compliqué qui repose sur l'intercommunication de plein
d'acteur⋅ices différent⋅es. Cependant, autoriser des communications de partout
peut causer des soucis de sécurité (on ne voudrait pas qu'un site aléatoire
puisse aller utiliser votre session avec le site de votre banque). Pour palier
cela, on déploie plusieurs outils.

D'abord, on ne peut contacter le backend qu'avec certains noms de domaine dans
l'URL. C'est la liste des `ALLOWED_HOSTS` qui permet de gérer cela. De base, on
aura au backend en tant que:
 - `api.${WEBSITE_HOST}`
 - `${WEBSITE_HOST}`
 - `dev.${WEBSITE_HOST}`

Ensuite, les CORS (*Cross-Origin Resource Sharing*) définissent quels autres
noms de domaine ont le droit de venir interagir avec nous. Cela permet notamment
au frontend de nous passer des informations d'authentification
(`CORS_ALLOW_CREDENTIALS` vaut `True`), et d'effectuer des requêtes
(`CORS_ALLOWED_ORIGINS`).

Enfin, on indique à Django quel module contient la liste des URLs de l'API dans
`ROOT_URLCONF`.

Ensuite viennent les CSRF, qui permettent d'éviter les attaques de *Cross-Site
Request Forgery*. C'est un mécanisme via lequel le navigateur va obtenir un
cookie via une requête à un point d'API, puis l'utiliser dans un appel pour
prouver sa bonne foi.

On peut contrôler quels noms de domaines sont autorisés à effectuer ces requêtes
de CSRF, et nous avons notamment besoin que le frontend y soit autorisé. On a du
coup:
```python
CSRF_TRUSTED_ORIGINS = [
    "https://api." + getenv("WEBSITE_HOST", "localhost"),
    "https://" + getenv("WEBSITE_HOST", "localhost"),
]
```

## Applications & Middlewares

Django est un framework explosé en de nombreux petits morceaux. On les réunit
ensuite pour apporter les fonctionnalités que l'on veut.

Les applications sont listées comme des chemins vers des modules dans
`INSTALLED_APPS`.

Les middleware, eux, sont listés dans `MIDDLEWARE`, et seront automatiquement
chargés.

## Bases de Données

Pour configurer les bases de donnée, la variable `DATABASES` agit comme un
dictionnaire. Django utilisera la base de donnée décrire dans le dictionnaire
contenu dans la clef `"default"`.

Dans notre cas, nous configurons la base de donnée PostgreSQL avec toutes les
informations d'authentification nécessaire pour pouvoir aller toucher la bonne
base de donnée via les variables d'environnement:
 - `DB_USER`: le nom de l'utilisateur⋅ice
 - `DB_NAME`: le nom de la base de donnée. Lors des tests, le suffixe `_test`
     est rajouté, pour que l'on aille mettre n'importe quoi dans une base de
     donnée qui ne soit pas celle de production
 - `DB_PASS`: le mot de passe pour le compte utilisé
 - `DB_HOST`/`DB_PORT`: Le nom d'hôte et le port du serveur qui héberge la base
     de données

Il est possible de configurer plusieurs bases de données, notamment une base de
donnée de backups.

## Authentification

Les utilisateur⋅ices dans une application Django doivent être décrit⋅es par un
*modèle Utilisateur*. Chez nous, il est stocké dans le module
[`user`](../../03-existant/modules/user.md), dans la classe `User`. On affecte
donc `"user.User"` à `AUTH_USER_MODEL`.

Des validateurs, qui permettent de vérifier des contraintes sur les mots de
passe, sont ensuite fournis à `AUTH_PASSWORD_VALIDATORS`. Ils vérifient que le
mot de passe est assez fort, et qu'il n'appartient pas à des listes de mot de
passes fréquemment utilisés.

## Traduction

On configure tout ce qui est lié à la traduction dans la configuration du projet
comme décrit [ici](../../03-existant/traductions.html#boilerplate-global).

## Contenus Statiques

Le backend Django doit souvent servir du contenu dit « statique », c'est à dire
du contenu qui ne changera pas. Cela englobe souvent les images et autres
assets, comme par exemple les logos des partenaires, les avatars des
utilisateur⋅ices, etc.

Ce contenu est placé dans un dossier dédié à cet effet, qui est indiqué dans une
variable de la configuration appelé `STATIC_ROOT`, et qui prend pour valeur
celle de la variable d'environnement du même nom. On liste ensuite l'ensemble de
tous les dossiers de statique possible dans `STATICFILES_DIRS`, et on indique à
Django à quelle URL la racine des statiques est censée correspond
(`STATIC_URL`).

## Login, Logout

En général, seul⋅es les membres du staff qui gèrent les informations du site ont
besoin de se login au backend, en général pour utiliser le panel admin.

On doit indiquer à Django trois choses:
 - L'URL qui sert à effectuer le login (`LOGIN_URL`)
 - L'URL vers laquelle DRF renvoie l'utilisateur⋅ice qui a réussi un login
     (`LOGIN_REDIRECT_URL`)
 - L'URL de logout (`LOGOUT_URL`)

## Email

Le backend est sensé être capable d'envoyer des emails, notamment pour pouvoir
valider les informations d'un compte avant la finalisation de son inscription.

Pour cela, il faut fournir tout un tas d'information au backend sur où et
comment s'authentifier pour envoyer des emails (avec quel compte, quel préfixe
pour les subjet lines, etc).

On a pour cela:

| Variable | Utilisation |
|-----------------|-------------|
| `host` | Nom de domaine du serveur mail |
| `pass` | Mot de passe pour s'authentifier |
| `from` | Adresse d'origine des mails |
| `port` | Port de connexion |
| `ssl` | Indique qu'il faut chiffrer la communication avec le serveur |
| `EMAIL_SUBJECT_PREFIX` | Préfixe des subjet lines des emails |

Il est possible de configurer plusieurs serveurs de mail, notamment pour les
différencier les mails tournois des mails de validation de compte. C'est pour
cela que ces informations sont stockées dans un dictionnaire dans la variable
`EMAIL_CONFIG` du fichier d'environnement :

```json
MAIL_AUTH='{
    "contact": {
        "from": "noreply@insalan.fr", 
        "pass": "localhost",
        "host": "localhost",
        "port": 53,
        "ssl": true
    }, 
    "tournament":{
        "from":"noreply@insalan.fr", 
        "pass":"localhost",
        "host":"localhost",
        "port": 53,
        "ssl": true
    }
}'
```

La variable `EMAIL_SUBJECT_PREFIX` est quant à elle spécifiée dans le fichier de
configuration du projet.

<!--
vim: set tw=80 spell spelllang=fr:
-->
