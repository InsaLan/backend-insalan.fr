# Manuel

## Deploiement automatique

Le manuel est déployé automatiquement à chaque tag sur le dépôt
[InsaLan/backend](https://github.com/InsaLan/backend-insalan.fr) via de
l'[intégration continue](https://fr.wikipedia.org/wiki/Int%C3%A9gration_continue) 
avec GitHub Actions.

Il est ensuite accessible à l'adresse [docs.insalan.fr](https://docs.insalan.fr/) mais vous devriez déjà le savoir, puisque vous êtes en train de le lire.

## Deploiement manuel

Pour déployer le manuel manuellement (rha, dûr à dire), il faut d'abord installer [mdBook](https://github.com/rust-lang/mdBook). mdBook est un outil de génération de documentation à partir de fichiers Markdown.

Il est possible de l'installer via `cargo`, le gestionnaire de paquets de Rust, ou avec un paquetage pour votre distribution.

Pour générer le manuel, il suffit de se placer dans le dossier `manuel` et de lancer la commande `mdbook build`. Le manuel sera généré dans le dossier `manuel/book` sous forme de pages HTML (du web, donc, comme toujours).
