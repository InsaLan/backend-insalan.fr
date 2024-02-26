# Docker de Production

Il n'y a très peu de différences entre le déploiement en développement et le
déploiement en production. La seule différence notable est que le déploiement en
production utilise d'autres images Docker (donc un autre docker compose) et que
le fichier de configuration (.env) est différent.

## Docker Compose Prod

Les mêmes commandes que pour le déploiement en développement sont utilisées,
mais avec un autre fichier de configuration. Pour lancer le docker compose en
production, il faut utiliser le fichier `docker-compose.yml`:

```shell
docker compose -f docker-compose.yml build
docker compose -f docker-compose.yml up -d
```

## Développer

Attention néanmoins, le déploiement en production ne doit pas être utilisé pour
développer. Le hot reloading (actualisation automatique du code) n'est pas
activé, et les images Docker sont plus lourdes à construire. Il est préférable
de développer en utilisant le déploiement en développement à part si vous aimer
souffrir.