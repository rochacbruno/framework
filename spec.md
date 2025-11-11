# Framework

Creates New django repositories based on templates

## Usage

Directy from git

```
uvx git+https://github.com/rochacbruno/framework init
```

Locally installed
```
uv tool install git+https://github.com/rochacbruno/framework

framework init
```

## What it does:

### Preflight

1. Run on the current directory or on the provided path as first argument to the command.
2. If pyproject already exists it exits.
3. If a local `templates` directory is found it runs based on that path, otherwise set remote git as the template source.

### Templating

1. Run copier on `templates/project`, this templates the root directory of the repository, it includes the pyproject.toml, manage.py and a `{{project}}` folder.
    a. This folder SHOULD NOT be edited manually by service developers, including the pyproject.toml
2. Run copier on `templates/service` for each service that user wants to bootstrap.
    a. by default it templates a single service,
       user can pass `--services` to the cli to bootstrap more services.
    b. User can use the cli `framework addservice` later to bootstrap additional services.
    c. Service folders CAN be edited by the developers, so this is only bootstrapped once, subsequent `framework update` will not template the service folders.
    d. Update can spawn post actions to do bulk changes on service folders, but not using copier as those files are the ones edited by developers.
3. Writes .framework.lock file as a state management, this file stores last time framework executed, references to each service application inside the project.
4. last step on the `update` workflow is to consolidate the extra dependencies coming from the optional `service.toml` so the developers can declare extra settings.
