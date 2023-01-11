# Redesign_insalan.fr
c'est comme /insalan.fr, en pas pareil (pas en php)

#How to
First, enter in the python venv: `source env/bin/activate`

if you want to create a new module, run `django-admin startapp your-new-app` in the `insalan` directory.

# Backend

framework used: https://www.django-rest-framework.org

# Architecture
The architecture of the project is the following:
```
├── LICENSE
├── README.md
├── db.sqlite3
├── env
├── insalan
│   ├── __init__.py
│   ├── asgi.py
│   ├── pizza
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── migrations
│   │   ├── models.py
│   │   ├── tests.py
│   │   └── views.py
│   ├── settings.py
│   ├── urls.py
│   ├── user
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── migrations
│   │   ├── models.py
│   │   ├── tests.py
│   │   └── views.py
│   └── wsgi.py
└── manage.py
```
`insalan` is the root directory of the web application.
`pizza`, `user` are apps in the Django language. There are the micro-services that implement specific features of the application.

For instance, `user` handles user-related actions (permission, authentication, etc...) and `pizza` handles the pizza application in the former website.




# Roadmap

## Backend

### Modules
- [ ] [user](insalan/user)
- [ ] [pizza](insalan/pizza)
- [ ] tournament
- [ ] payment
- [ ] placement
- [ ] langate
- [ ] admin
## Frontend

