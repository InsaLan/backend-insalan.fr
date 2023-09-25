# Introduction

Ce manuel contient les informations nécessaires pour prendre en main le projet
du "backend" du site de l'InsaLan.

On commencera par expliquer pourquoi ce projet a été commencé, les technologies
utilisées, et comment faire et modifier des choses.

## Il fut un temps…

Jusqu'à 2023, le site web de l'InsaLan tournait sur une base de code [PHP avec
Symfony](https://symfony.com/). Suite à un désintérêt prononcé et persistent au
fur et à mesure des années, et des passations de plus en plus décousues,
l'équipe web est tombé à un effectif d'une personne, avec au total deux ou 3
membres encore actives qui connaissaient le fonctionnement approximativement de
la base **gargantuesque** de code du site. Aucun effort n'a été entrepris pour
maintenir les versions du code à jour jusqu'au moment où Symfony 3, puis 4, sont
arrivées en fin de vie. S'en sont suivies deux migrations d'urgence qui ont
sévèrement cassé le vieux site avant de pouvoir avoir à nouveau une version
stable.

En plus de cela, l'ancien site n'offrait aucune protection anti-bot, ce qui a
conduit à des vagues de milliers de faux comptes créés, et nos adresses mail qui
se sont faites recensées comme servant à du spam auprès de OVH (qui nous fournit
le service mail). Cela a tellement impacté le site web que le bureau de la XVII
a dû valider les inscriptions et lister les paiements des 400 joueur⋅euses et
manager⋅euses à la main. Ajouter une
[CAPTCHA](https://fr.wikipedia.org/wiki/CAPTCHA) n'était pas faisable vu l'âge
de la base de code, et le problème allait continuer.

Il fallait absolument un nouveau site.

## Le Projet de Refonte

En 2022, [Mahal](https://github.com/ShiroUsagi-San) a décidé de diriger un
effort collectif regroupant plusieurs personnes déjà présentes et connues dans
l'association au niveau des équipes SysRez, Web et Tournois, ainsi que parmis
des vieux et vieilles con⋅nes de ces équipes, pour monter une refonte du site
web. Les objectifs principaux étaient:
 - Dépoussiérer la base de code pour avoir une structure claire, connue, et
     documentée
 - Avoir un projet qui peut être repris par des étudiant⋅es de l'INSA
 - Utiliser des langages qui permettent de facilement prendre en main le projet
 - Fortifier la vérification du code en utilisant des technologies
     d'[intégration continue](https://fr.wikipedia.org/wiki/Int%C3%A9gration_continue)
 - Avoir un site à minima fonctionnel pour l'édition XVIII

Ainsi, nous avons travaillé à concevoir et implémenter la base de code, de
Janvier à Octobre 2023, et la voici.

## L'équipe Original, ce Manuel

À l'issu de la période de développement embryonique du projet, l'équipe
originale, dont l'auteur⋅ice de ce manuel faisait parti⋅e, a commencé à déployer
le projet en « pré-production », à le tester, et à documenter la prise en main.

Étant donné que le backend (càd. la partie en charge de toute la logique et les
opérations sur les données) du site repose sur des tactiques d'un système
logiciel relativement mal documenté, voici un manuel qui, nous l'espérons,
permettra de répondre aux problèmes initiaux de prise en main.

---

Ce manuel est présenté tel quel, sans garantie aucune qu'il ne vous fera pas
désinstaller tout votre système d'exploration ou effacer vos précieuses photos
de vacance chez mémé Géraldine.

Comme il faut faire les choses proprement et mettre des licenses, on va dire que
ce manuel est sous [Creative Commons BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/), ce qui est *OK*.

---

L'équipe originale de développement qui a conduit à ce manuel était composée de:
 - Téo "Mahal" Nespoulet [il], président de l'InsaLan XVI
 - Paul "TheBloodMan" Gasnier [il], responsable SysRez-Dev de l'InsaLan XVIII
 - "Khagana" [il], responsable SysRez-Infra de l'InsaLan XVIII
 - "somebody" [il], péon SysRez-Dev de l'InsaLan XVIII
 - Amélie "Lymkwi" Gonzalez [æl|elle], responsable SysRez de l'InsaLan XVI
 - Aurore "Lugrim" Poirier [ælle|elle], responsable Web de l'InsaLan XIV

<!-- vim: set cc=80 tw=80: -->
