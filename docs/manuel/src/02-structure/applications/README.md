# Applications

Les fonctionnalités du backend sont fournies via des **applications**, qui sont
les unités de code en charge de gérer une tâche ou un ensemble de tâches
proches.

Dans l'idée, ce sont en gros des modules.

Il y a un module pour gérer le paiement, un module pour gérer les users, un
module pour gérer les tournois, etc.

Un module est organisé en plusieurs parties dans notre projet DRF. Il y a:
 - des [modèles](./modeles.md) pour représenter nos objets
 - des [vues](./vues.md) pour rassembler les objets et traiter des demandes de
     l'API
 - des [serializers](./serializers.md) pour transformer les objets en chaînes de
     caractère, et inversement
 - des [endpoints](./endpoints.md) pour que les utilisateur⋅ices puissent venir
     faire des requêtes sur le backend

Ces éléments forment une espèce de pile, qui permettent le traitement des
données des objets, entre l'API exposée à internet d'un côté, et la base de
donnée qui contient les modèles de l'autre.

<!--
vim: set tw=80 spell spelllang=fr:
-->
