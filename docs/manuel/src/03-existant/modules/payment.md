# Payment

## Introduction

Alors là, on est pas franchement sur la partie la plus sympa du backend. Mais
c'est important de comprendre comment ça marche, parce que c'est un peu le nerf
de la guerre. Pas de paiements, pas d'inscription. Pas d'inscription, pas de
LAN. Pas de LAN, pas de LAN.

Les modèles de ce module sont assez compliqués parce qu'ils dépendent de notre
prestataire de paiement, HelloAsso. On a donc un modèle `Product` qui représente
un produit achetable (un tournoi, un repas, une place de LAN, etc.), un modèle
`Transaction` qui représente une transaction (un paiement), et un modèle
`Payment` qui représente un paiement (un paiement).

## Product

Les produits n'on pas à être créés manuellement, ils sont générés
automatiquement à la création d'un tournoi (et plus tard, d'un créneau pizza).
Ils contiennent plusieurs info comme le nom, le prix, la description, les dates
de début et de fin de vente, etc.

## Discount

Les réductions sont créées manuellement par les admins. Elles font le lien entre
un utilisateur et un produit. La valeur de la réduction et une description sont
également stockées dans ce modèle. Les réductions doivent être ajoutés en amont
du paiement et peuvent être utilisées une seule fois. Cela peut permettre de
réduire le prix d'un pour certains joueurs. 

## Transaction

Les transactions sont créées à chaque fois qu'un utilisateur initie un paiement
avec HelloAsso. Elles contiennent des informations sur le paiement, comme le
montant, le produit acheté, l'utilisateur qui a acheté, etc. Une transaction
peut très bien ne pas être suivie d'un paiement, si l'utilisateur abandonne le
paiement en cours de route.

## Payment

Les paiements sont créés à chaque fois qu'un utilisateur a payé un produit. Ils
contiennent des informations sur le paiement, comme le montant, le produit
acheté, l'utilisateur qui a acheté, etc. Attention, un paiement peut se
transformer en remboursement si l'utilisateur annule son achat.

## HelloAsso

HelloAsso est notre prestataire de paiement. C'est une plateforme qui permet de
faire des paiements en ligne, et qui est spécialisée pour les associations.
Cette brique est techniquement changeable pour une autre (si jamais l'amicale
décide de forcer pour utiliser Lifpay) mais pour l'instant, c'est HelloAsso qui
nous convient le mieux.