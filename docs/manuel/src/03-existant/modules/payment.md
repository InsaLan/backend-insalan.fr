# Payment

## Introduction

Alors là, on est pas franchement sur la partie la plus sympa du backend. Mais
c'est important de comprendre comment ça marche, parce que c'est un peu le nerf
de la guerre. Pas de paiements, pas d'inscription. Pas d'inscription, pas de
LAN. Pas de LAN, pas de LAN.

## Modèles

Les modèles de ce module sont assez compliqués parce qu'ils dépendent de notre
prestataire de paiement, **HelloAsso**.

### Product

Ces objets représentent des produit achetables (un tournoi, un repas, une place de LAN, etc.). Ils n'ont pas à être créés manuellement, ils sont **générés
automatiquement** à la création d'un tournoi (et plus tard, d'un créneau pizza).
Ils contiennent plusieurs info comme le nom, le prix, la description, les dates
de début et de fin de vente, etc.

### Discount

Les réductions sont créées manuellement par les admins. Elles font le lien entre
un utilisateur·rice et un produit. La valeur de la réduction et une description sont
également stockées dans ce modèle. Les réductions doivent être ajoutés en amont
du paiement et peuvent être utilisées une seule fois. Cela peut permettre de
réduire le prix d'un pour certains joueurs. 

### Transaction

Les transactions sont créées à chaque fois qu'un utilisateur·rice **initie un paiement**
avec HelloAsso. Elles contiennent des informations sur le paiement, comme le
montant, le produit acheté, l'utilisateur·rice qui a acheté, etc. Une transaction
peut très bien ne pas être suivie d'un paiement, si l'utilisateur·rice abandonne le
paiement en cours de route.

### Payment

Les paiements sont créés à chaque fois qu'un utilisateur·rice **a payé un produit**. Ils
contiennent des informations sur le paiement, comme le montant, le produit
acheté, l'utilisateur·rice qui a acheté, etc. Attention, un paiement peut se
transformer en remboursement si l'utilisateur·rice annule son achat.

## Procédure de paiement

### API HelloAsso

HelloAsso est notre prestataire de paiement. C'est une plateforme qui permet de
faire des paiements en ligne, et qui est spécialisée pour les associations.
Cette brique est techniquement **changeable pour une autre** (si jamais l'amicale
décide de forcer pour utiliser Lyfpay) mais pour l'instant, c'est HelloAsso qui
nous convient le mieux.

Pour envoyer une demande de paiement, on utilise l'**API HelloAsso**, dont les clés sont normalement dans le `.env`. Sa documentation peut être trouvée [ici](https://dev.helloasso.com/docs/introduction-%C3%A0-lapi-de-helloasso).

### PayView

La vue PayView, déclarée dans `insalan/payment/views.py` est celle qui s'occupe de déclarer un **"checkout intent"**. Cet intent est celui qui déclare une demande de paiement faite à un utilisateur·rice, et il est envoyé sous la forme d'une requête POST sur https://api.helloasso.com/v5/organizations/insalan/checkout-intents. C'est cette vue qui est appelée par le front quand l'utilisateur·rice clique sur le bouton "Payer" de son panier. Cette vue est aussi celle qui crée l'objet `Transaction` lié au paiement.

### Notifications

L'API HelloAsso communique avec notre site par "notifications", des requêtes POST envoyées sur une addresse spécifiée dans les paramètres du compte HelloAsso de l'InsaLan. En l'occurence, il s'agit de https://api.insalan.fr/v1/payment/notifications, et de la vue `Notifications`. Ces notifications peuvent concerner plusieurs choses, comme des changements apportés au compte HelloAsso, ou au fonctionnement d'HelloAsso en lui-même.

Cependant, les notifications qui nous intéressent vraiment sont celles concernant les paiements. Tout d'abord, une fois que l'utilisateur·rice a **validé ses informations de paiement**, une première notification comme [celle-ci](https://dev.helloasso.com/docs/notification-exemple#commandes-cr%C3%A9%C3%A9-sur-un-paiement-checkout-avec-des-%C3%A9ch%C3%A9ances) avec `eventType = "Order"` est envoyée. Celle-ci crée l'objet `Payment` du paiement. C'est aussi lors du traitement de cette notification qu'on récupère le nom du·de la joueur·euse, qui nous sera utile pour vérifier saon identité à l'entrée. On met aussi `confirm_name` à `True` pour qu'iel confirme que c'est bien saon identité.

Ensuite, lorsque **la carte a bien été débitée** et que la thune du·de la joueur·euse est officiellement la notre, une notification de [ce genre](https://dev.helloasso.com/docs/notification-exemple#paiement-autoris%C3%A9-sur-un-checkout) est envoyée. C'est celle-ci qui va venir valider la `Transaction` (ou l'invalider, puisque ces notifications informent aussi des éventuelles erreurs comme les paiements refusés).