# Framework

Framework initializes Django projects based on templates and keep project updated
to follow the defined standards.

## Features

- Bootstrap new projects with `init`.
- Bootstrap new apps for the project with `init --apps`.
- Keep project updated with latest changes.
- Leave `apps/*` untouched so developers can edit it.
- Consolidates meta files such as pyproject, sonar, pre-commit, github actions, settings based on template standards + apps customizations.
- Validate the whole project structure.


## Requirements

- git
- uv

## usage

### Start a new project named `my-project` with a single app named `api`

```console
$ uvx git+https://github.com/rochacbruno/framework init my-project
...
…………………………………………………………………………………………………………
Framework init finished
Created project at my-project/my_project
Created apps at my-project/apps/[api]
```
```
my-project
# Editable by developers
├── apps
│   ├── metadata/{pyproject,README,sonar,docs, AGENTS}
│   └── api/{viewsets,serializers,urls,permissions,settings...}.py

# Everything from here is not editable, will be overwritten by framework updates.
├── my_project
│   ├── asgi.py
│   ├── __init__.py
│   ├── settings.py
│   ├── tests
│   ├── urls.py
│   └── wsgi.py
├── docs
│   └── templates
├── LICENSE
├── manage.py
├── AGENTS.md
├── pyproject.toml
├── README.md
└── sonar-project.properties
```

> Developers now can edit any file inside `apps` folder, this is the only folder unmanaged by subsequent framework updates, framework will consolidate the content of `apps/metadata` into the respective root folder file.
