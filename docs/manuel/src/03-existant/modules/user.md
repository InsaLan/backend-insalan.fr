# User

## Introduction

Le module User est le module qui gère les utilisateurs, les groupes et les
permissions. Une grande partie de ce module est gérée par Django, mais il y a
quelques spécificités qui sont propres à notre application.

## Utilisateurs

Les utilisateurs sont les personnes qui utilisent l'application. Ils peuvent
être des joueurs, des administrateurs, ou des modérateurs. Chaque utilisateur a
un nom d'utilisateur, un mot de passe, une adresse email, et un nom complet. Ils
peuvent aussi avoir un avatar, des pronoms,...

## Permissions

Les permissions sont des droits que l'on peut donner à un utilisateur. Elles
permettent de définir finement les droits d'un utilisateur. Par exemple, on peut
donner la permission "Ajouter un tournoi" à un utilisateur, ou la permission
"Modifier un tournoi".

## Groupes

Les groupes sont des permissions regroupées. Ils permettent de donner des
ensembles de permissions à un utilisateur. Par exemple, le groupe "Equipe
tournois" peut avoir accès à tout ce qui est relatif à la gestion des tournois.
