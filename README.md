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
- [ ] [user](user) @lugrim
	- [ ] placement
	- [ ] langate @lux
	- [ ] tournament 
- [ ] admin @mahal
- [ ] payment
- [ ] archive
- [ ] connectors 
- [ ] [pizza](pizza)
## Frontend
@mahal
framework used: vuejs

