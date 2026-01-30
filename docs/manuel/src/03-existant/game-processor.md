# Game Processor

## Introduction

Le système de **Game Processor** (ou "processeur de jeu") est un mécanisme
d'automatisation qui permet de gérer automatiquement les tournois pour certains
jeux via leurs APIs officielles. Concrètement, ça évite de devoir créer les
lobbies manuellement, récupérer les résultats, et mettre à jour les scores à la
main.

Actuellement, le système supporte :
- **League of Legends** via l'API Tournament v5 de Riot Games
- **Mode vide** pour les jeux sans automatisation

## Architecture

### Classe Abstraite `GameProcessor`

Tous les processeurs de jeu héritent de la classe abstraite `GameProcessor` qui
définit les hooks (points d'entrée) suivants :

```python
class GameProcessor(ABC):
    short: ClassVar[str]  # Identifiant court (ex: "LoL")
    name: ClassVar[StrPromise]  # Nom affiché (ex: "League of Legends")
    
    # Paramètres configurables
    default_game_parameters: ClassVar[dict[str, Any]] = {}
    game_parameters_schema: ClassVar[dict[str, dict[str, Any]]] = {}
    
    # Hooks du cycle de vie
    @abstractmethod
    def initialize_tournament(tournament: BaseTournament) -> dict[str, Any] | None
    
    @abstractmethod
    def update_tournament(tournament: BaseTournament) -> dict[str, Any] | None
    
    @abstractmethod
    def create_match(match: Match) -> dict[str, Any] | None
    
    @abstractmethod
    def start_match(match: Match) -> dict[str, Any] | None
    
    @abstractmethod
    def process_result_match(match: Match, payload: dict[str, Any]) -> dict[str, Any] | None
    
    @abstractmethod
    def delete_match(match: Match) -> None
```

### Cycle de Vie d'un Tournoi

```
1. Création du Tournament
   └─> initialize_tournament() appelé automatiquement
       └─> Récupération des données nécessaires selon le jeu

2. Action admin "Rafraîchir API"
   └─> update_tournament() appelé manuellement
       └─> Mise à jour des données API si nécessaire

3. Création d'un Match (bracket/group/swiss)
   └─> create_match() appelé automatiquement
       └─> Création de matches via l'API du jeu

4. Démarrage d'un Match
   └─> start_match() appelé lors du passage en ONGOING
       └─> Lancement du match via l'API du jeu

5. Réception des Résultats (callback API)
   └─> process_result_match() appelé par les endpoints /result
       └─> Mise à jour des scores et progression du tournoi

6. Suppression d'un Match
   └─> delete_match() appelé lors de la suppression
       └─> Nettoyage des ressources
```

### Configuration des Paramètres de Jeu

Chaque processeur peut définir des paramètres configurables via
`default_game_parameters` et `game_parameters_schema`. Ces paramètres sont
stockés dans le champ JSON `Game.games_parameters` et peuvent être modifiés dans
l'admin. Cela permet d'adapter le comportement du processeur selon les besoins
(ex: type de carte, mode de jeu, etc.).

## Implémentation League of Legends

### Configuration

Le processeur LoL utilise trois paramètres configurables dans
`Game.games_parameters` :

| Paramètre | Type | Valeurs | Par défaut | Description |
|-----------|------|---------|------------|-------------|
| `mapType` | choice | `SUMMONERS_RIFT`, `HOWLING_ABYSS` | `SUMMONERS_RIFT` | Carte de jeu |
| `pickType` | choice | `BLIND_PICK`, `DRAFT_MODE`, `ALL_RANDOM`, `TOURNAMENT_DRAFT` | `TOURNAMENT_DRAFT` | Mode de sélection |
| `spectatorType` | choice | `NONE`, `LOBBYONLY`, `ALL` | `ALL` | Type de spectateur |


## Configuration dans l'Admin

### Niveau Game

Dans le panel admin, lors de la création/édition d'un `Game` :

1. Sélectionner le **game_processor** (None, LoL, etc.)
2. Si LoL sélectionné, un widget apparaît pour configurer **games_parameters**
3. Les paramètres par défaut sont appliqués automatiquement
