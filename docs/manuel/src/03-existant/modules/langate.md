# Langate

Le module `langate` a été développé pour répondre à un besoin absolument vital:
authentifier les utilisateur⋅ices du portail captif *Langate* lors de
l'événement.

## Qu'est-ce qu'un Langate et pourquoi s'infliger cela ?

Le [*Langate2000*](https://github.com/InsaLan/langate2000) ou Langate est le
portail captif utilisé par l'InsaLan lors des événements (Mini ou autre) pour
authentifier les utilisateur⋅ices. Cela permet deux choses importantes:
 - N'autoriser l'accès au réseau qu'aux personnes ayant payé leur entrée
 - Associer une connexion au réseau avec un pseudo, pour des besoins légaux de
     traçabilité (nous agissons ici en qualité de fournisseur d'un service
     internet). Si la justice impute une activité illégale à une connexion qui
     sort de chez nous, nous devons pouvoir prouver qu'il s'agit d'une personne
     identifiable ayant enfreint nos règlements, et non l'association en
     elle-même

Ainsi, le Langate tourne localement dans l'infrastructure de Cœur de Réseau
(CdR) pour filtrer l'accès à Internet et gérer les authentifications.

Lors des Minis (du moins jusqu'en 2023), le Bureau se chargeait de créer les
comptes autorisés sur le Langate lors du paiement d'une entrée. Lors des
événements, cependant, pour simplifier la vie de tout le monde, les comptes ne
sont pas créés manuellement. À la place, le Langate interroge le site web de
l'InsaLan lors de la première connexion au portail avec un certain login, et le
mot de passe associé. Si le combo login et mot de passe est valide sur le site,
alors le site fournit les informations nécessaires au Langate pour créer un
compte local pour cet⋅te utilisateur⋅ice. Si ce n'est pas le cas, le site
fournit, autant que possible, la raison pour laquelle la création ne peut pas
avoir lieu (par exemple, mauvais mot de passe, place pas payée, …).

Pour pouvoir recevoir ces informations, le Langate a besoin que le site web de
l'InsaLan expose un chemin d'API spécifique via lequel il peut aller extraire
ces données. C'est le rôle du module `langate` d'aller exposer et répondre à ce
point d'API.

## Le Fonctionnement

Le point d'API utilisé est `/v1/langate/authenticate` en verbe `POST`. Le
Langate peut choisir d'effectuer un `POST` vide, ou de fournir un objet au
format JSON qui contient un seul champs. Par exemple:
```json
{ "event_id": 7 }
```

Le champs `"event_id"` permet d'indiquer au site web le numéro de l'événement en
cours pour lequel l'utilisateur⋅ice est enregistré. Comme il peut y avoir
plusieurs événements en cours, et qu'un⋅e utilisateur⋅ice a le droit de
s'inscrire une seule fois en tant que joueur⋅euse et une seule fois en tant que
manager à chaque événement, il faut pouvoir discerner dans quel événement
chercher sa place.

Si aucune donnée n'est fournie mais qu'il n'y a qu'un seul événement en cours,
alors le module cherchera dans cet événement. Si aucun évènement n'est en cours,
le backend lancera une erreur de mauvaise requête (`HTTP 400`). Si plusieurs
événements sont en cours, et que le Langate ne spécifie pas lequel utiliser,
alors le site répondra qu'il ne sait pas où chercher (`HTTP 400`).

En cas de succès, le backend commence à calculer la réponse.

### Réponse

Le site web répond un objet JSON qui décrit:
 - Les informations sur l'utilisateur⋅ice (nom, prénom, email, etc) pour pouvoir
     créer son compte en local
 - Une erreur potentielle (`"err"`) si la place n'est pas payée ou qu'aucune
     n'est trouvée
 - Si des places sont trouvées, alors on retournera une liste d'entrées, une par
     tournois avec une inscription. La quantité d'inscription étant limitée à
     une en tant que joueur et une en tant que manager, la liste est forcément
     limitée en taille. Chaque entrée dans la liste contient:
     - Le nom de code du jeu du tournois (par exemple: `"CSGO"`)
     - Le nom complet du jeu: (par exemple: `"Counter-Strike: Global Offensive"`)
     - Le numéro identifiant de la Team pour laquelle la place est enregistrée
     - Un booléen qui décrit si la place concerne un⋅e joueur⋅euse, ou un⋅e
         manager
     - Un booléen qui indique si la place a été payé⋅e

À partir du moment où au moins un des booléens indiquant si la place a été payée
est `false`, le site retournera une erreur indiquant qu'il faut aller payer sa
place. Le Langate se chargera d'aller transformer cela en message cohérent pour
la personne assise devant l'écran.

Voici la tête de l'objet JSON retourné:
```json
{
  "user": {
    "username": "theUser",
    "name": "John Doe",
    "email": "john@email.com"
  },
  "err": "err_not_found",
  "tournament": [
    {
        "shortname": "CSGO",
        "game_name": "Counter-Strike: Global Offensive",
        "team": 228,
        "manager": false,
        "has_paid": true
    }
  ]
}
```

<!--
vim: set tw=80 spell spelllang=fr:
-->
