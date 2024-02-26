# Configuration

Arf, la configuration. C'est ni plus ni moins que ce qui va déterminer le
comportement de votre application. Si elle va fonctionner ou non. Si elle va
être sécurisée ou non. Bref, c'est un peu important.

La configuration de votre application est stockée dans un fichier `.env` à la
racine de votre projet.***Normalement*** (et je dis bien normalement), si vous
avez copié le fichier `.env.dist` à la racine de votre projet, vous devriez
avoir une configuration par défaut qui fonctionne. Vous pouvez bien sûr la
modifier pour l'adapter à vos besoins.

Mais avant de vous lancer dans la modification de la configuration, il est
important de comprendre ce que chaque paramètre signifie. C'est ce que nous
allons voir dans cette section.

## Les paramètres d'environnement

### `DEV`

Ce paramètre permet de déterminer si l'application est en mode développement ou
non. Si ce paramètre est à `1`, alors l'application est en mode développement.
Si ce paramètre est à `0`, alors l'application est en mode production.

### `WEBSITE_HOST`

Ce paramètre permet de déterminer l'URL de votre site web. C'est important pour
générer des liens absolus dans votre application. Certaines valeurs sont
considérées comme des valeurs par défaut :
- `insalan.localhost` : si vous êtes en local
- `insalan.fr` : si vous êtes en production, sur le vps

Si vous avez un nom de domaine personnalisé, vous pouvez le renseigner ici.

### `API_VERSION`

Ce paramètre permet de déterminer la version de l'API. C'est aussi utilisé pour
générer des liens absolus dans votre application. Il n'y a pas de raison de
changer tant que nous ne changeons pas tout.

### `PLACEHOLDER`

Ce paramètre permet de déterminer si l'application doit être mis en mode
minimale ou non. Ce mode a été développé au cas où l'application ne serait pas
encore prête à être utilisée. Si ce paramètre est à `1`, alors l'application est
en mode minimal. Si ce paramètre est à `0`, alors l'application est en mode
normal.

### `PROD_NGINX_PORT`, `PREPROD_NGINX_PORT`, `EXTERNAL_NGINX_PORT`

Ces paramètres permettent de déterminer le port sur lequel l'application est
exposée. Ils sont utilisés pour que les différentes couches de l'application
puissent communiquer entre elles.

### `BACKEND_DJANGO_SECRET`

Ce paramètre est la clé utilisé par django. Une description plus détaillée est
disponible dans la section sur la [configuration du
projet](../02-structure/projet/configuration.md#secrets--debug).

### `BACKEND_STATIC_ROOT`, `BACKEND_MEDIA_ROOT`

Ces paramètres permettent de déterminer les dossiers où seront stockés les
fichiers statiques et les fichiers médias. Plus d'informations sont disponibles
dans les sections sur les [fichiers statiques](../02-structure/statiques.md) et
les [fichiers médias](../02-structure/media.md).

### `SESSION_COOKIE_AGE`

Ce paramètre permet de déterminer la durée de vie des cookies de session. Cette
variable a été ajouté tardivement pour pouvoir gérer de la même manière
l'expiration des cookies de session (ce qui fait qu'en rechargeant votre page
vous soyez toujours connecté) entre le frontend et le backend.

### `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_SUPERUSER`, `DB_SUPERPASS`

Tout ces paramètres permettent de déterminer les informations de connexion à la
base de données. Grosso modo, tant que ça fonctionne, pas besoin d'y toucher
mais c'est bien de savoir où ça se trouve.

### `MONGODB_PASS`, `MONGODB_USER`

Si vous avez bien lu les variables précédentes et la section sur la [pile
logicielle](../00-prelude/pile-logiciel.md#la-pile-logiciel), vous avez compris
que ces paramètres permettent de déterminer les informations de connexion à la
base de données MongoDB. Nous reviendrons sur l'utilité de mongo en abordant les
[contenus cms](./modules/cms.md).

### `SUPERUSER_USER`, `SUPERUSER_PASS`

Si vous démarrez le site avec une base de donnée vide sans ces paramètres, vous
serez bien embêté. Leur seul but est de créer un super utilisateur lors du
premier démarrage de l'application.

### `PROTOCOL`

Bien sûr, si vous êtes là, vous avez lu le prélude et vous savez ce que c'est
que le [protocole ou scheme](../00-prelude/prerequis.md#web-api-rest). Ce
paramètre permet de déterminer le protocole utilisé par l'application. Il est
utilisé pour générer des liens absolus dans votre application.

En théorie, il est à 'https' en production et 'http' en développement.

### `FRONTEND_NODE_ENV`

Celui là, c'est un peu comme [`DEV`](#dev) mais pour le frontend. Il permet de
déterminer si le frontend est en mode développement ou non. Si ce paramètre est
à `development`, alors le frontend est en mode développement. Si ce paramètre
est à `production`, alors le frontend est en mode production.

### `MAIL_AUTH`

Je vais pas faire l'affront de revenir sur le mailer, tout est dans la section
sur le [mail](../02-structure/projet/configuration.md#email).

### `HELLOASSO_HOSTNAME`, `HELLOASSO_ORG_SLUG`, `HELLOASSO_CLIENT_ID`, `HELLOASSO_CLIENT_SECRET`, `HELLOASSO_BACK_URL`, `HELLOASSO_RETURN_URL`, `HELLOASSO_ERROR_URL`

Alors ceux là, c'est pour notre prestataire de paiement. Ils servent pour nous
authentifier, spécifier les urls de retours (succès, erreur, annulation), et
pour spécifier l'organisation qui gère les paiements. Ils n'ont pas besoin
d'être correctement configuré pour que l'application fonctionne en développement
mais vous aurez des soucis si c'est le cas en production.

## Récap

Pfiou, c'était long. Mais maintenant vous devriez être capable de toucher au
fichier de configuration sans trop de soucis. Si vous avez des questions,
n'hésitez pas à demander au responsable Dev ou aux vieux.eilles con.ne.s de
l'asso, ils sont là pour ça.