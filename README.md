# Insalan backend

## Description

This is the backend of the Insalan website. It is a Django and Django rest
framework application. It is served by a Nginx server. It is part of the
[insalan.fr](https://insalan.fr) infrastructure and is deployed with the
[infra-insalan.fr](https://github.com/InsaLan/infra-insalan.fr) repository.

## Contributing

Please read carefully [the CONTRIBUTING.md file](CONTRIBUTING.md) before any
contribution.

## Run the backend in local

The backend has to be deployed from the docker-compose setup (so you need to
install it!). Please refer to [this
README](https://github.com/InsaLan/infra-insalan.fr/blob/main/README.md)

Once the docker-compose is running, you can access the frontend at
`http://api.beta.insalan.localhost` if you are using the default beta configuration.

## Architecture

`insalan` is the root directory of the web application.

`pizza`, `user`,... are apps in the Django language. They are micro-services
that implement specific features of the application.

For instance, `user` handles user-related actions (permission, authentication,
etc...) and `pizza` handles the pizza application.

Each apps have their own `urls.py` file that defines the routes of the app. The
endpoints are prefixed by the app name. For instance, the prefix to the pizza
app is `/api/{version}/pizza`
