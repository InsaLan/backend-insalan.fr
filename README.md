# How to
First, enter in the python venv: `source env/bin/activate`

if you want to create a new module, run `django-admin startapp your-new-app` in the `insalan` directory.

# Backend

framework used: https://www.django-rest-framework.org

# Architecture
`insalan` is the root directory of the web application.
`pizza`, `user` are apps in the Django language. They are micro-services that implement specific features of the application.

For instance, `user` handles user-related actions (permission, authentication, etc...) and `pizza` handles the pizza application in the former website.

The base api: `/api/version/endpoint`

for example, for the pizza module: `/api/version/pizza/`


# Roadmap

## Backend

### Modules
- [ ] authentication
- [ ] [user](user) [@Lugrim](https://www.github.com/Lugrim)
	- [ ] placement
	- [ ] langate [@Lux](https://www.github.com/Lymkwi)
	- [ ] tournament
- [ ] admin [@Mahal](https://www.github.com/ShiroUsagi-san)
- [ ] payment
- [ ] archive
- [ ] connectors
- [ ] [pizza](pizza) [@Khagana](https://www.github.com/ThibaultDidier)
- [ ] partos [@somebody](https://github.com/floflo0/)

## Frontend
[@Mahal](https://www.github.com/ShiroUsagi-san)
framework used: vuejs

