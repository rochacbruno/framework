import os
from pathlib import Path
from typing import Annotated

from copier import run_copy, run_update
from cyclopts import App, Parameter
from git import Repo

app = App(
    name="Framework",
    help="Framework for building Django applications",
)

REPO = os.getenv("FRAMEWORK_REPO", "https://github.com/rochacbruno/framework")


@app.command
def init(
    destination: Path | None = None,
    project: Annotated[str | None, Parameter(alias="-p")] = None,
    apps: Annotated[list[str], Parameter(consume_multiple=True)] = ["api"],
):
    """Initialize a new Django Project.

    ## Usage
    ```bash
    # New project on current folder with one app named api:
    framework init
    # New project on specific folder with one app named api:
    framework init /tmp/foo
    # New project on named folder with 3 apps:
    framework init my-service --apps api web core

    ```
    ---
    Args:
        destination: The root of the repository
        project: project name [default to destination folder name]
        apps: names for each app to be initialized
    """
    destination = destination or Path.cwd()
    project = project or destination.name.replace("-", "_")
    if not destination.exists():
        destination.mkdir(parents=True, exist_ok=True)
    if not Path(destination / ".git").exists():
        Repo.init(str(destination))

    print(f"Initializing your project on {destination}")
    run_copy(
        REPO,
        destination,
        data={
            "project_name": project,
            "template": "templates/project",
        },
    )
    print("Main project created.")

    apps_destination = destination / "apps"
    for app_name in apps:
        run_copy(
            REPO,
            apps_destination / app_name,
            data={
                "template": "templates/app",
            },
        )
        print(f"Created app {app_name}")

    if apps:
        # Ensure apps is a Python module so each app can be imported
        Path(apps_destination / "__init__.py").touch()

    print("…" * 40)
    print("Framework init finished")
    print(f"Created project at {destination}/{project}")
    if apps:
        print(f"Created apps at {destination}/apps/[{','.join(apps)}]")


@app.command
def update(destination: Path | None = None):
    """Update an existing application"""
    destination = destination or Path.cwd()
    print(f"Updating your app on {destination}")
    run_update(
        destination,
        overwrite=True,
        skip_answered=True,
    )


@app.command
def validate(destination: Path | None = None):
    """Validate an existing application"""
    destination = destination or Path.cwd()

    print(f"Validating your app on {destination}")


@app.command
def completions():
    """generate shell completions."""
    print(app.generate_completion())
