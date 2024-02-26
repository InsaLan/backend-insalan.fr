# tickets

## Introduction

Le module `tickets` est un module qui permet de gérer les,... tickets.
C'est-à-dire les billets d'entrée pour les événements de l'association et
potentiellement plus tard de permettre les commandes de pizza en ligne. Il
permet de créer des types de billets, de les scanner, de les annuler, etc.

## Billets

Les billets sont les tickets d'entrée pour les événements. Chaque billet est
juste un lien entre un utilisateur, un tournois, un token unique et un status.
Il peut être scanné pour vérifier son authenticité.