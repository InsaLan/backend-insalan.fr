# CMS

## CM-Quoi ?

Qu'est-ce que c'est donc que cette carabistouille de CMS ? C'est un acronyme
pour Content Management System, ou Système de Gestion de Contenu en français.
C'est un module qui permet de gérer le contenu du site web. C'est-à-dire les
pages, les articles, les événements, les actualités, etc.

## Utilité

Le principal avantage du CMS est de pouvoir modifier le contenu du site web sans
avoir à toucher au code de l'application. C'est très pratique pour les personnes
qui ne sont pas développeurs, mais qui veulent pouvoir modifier le contenu du
site web. Par exemple, les membres du bureau de l'association, ou les
organisateurs d'événements. C'est aussi très pratique pour les développeurs, car
ça permet de déléguer la gestion du contenu à des personnes qui ne sont pas
développeurs.

## Fonctionnalités

Il y a trois type de contenu CMS, les `contents`, les `constants` et les
`files`. Les `contents` sont des éléments de contenu qui sont affichés sur le
site web et qui peuvent dépendre de constantes qui sont justement définies à
part. Les `files` sont des fichiers uploadés sur le site web. Ils peuvent être
des images, des vidéos, des documents, etc.

## Spécificités

Les contenus CMS ne sont pas enregistrés dans la base de données de
l'application, mais dans une base de données mongoDB dédiée. Cela permet de ne
pas surcharger la base de données principale avec des contenus qui peuvent être
très volumineux.

Tout les contenus CMS sont récupéré en même temps à ouverture du site web. Il
est donc important de ne pas surcharger la base de données mongoDB avec des
contenus inutiles.