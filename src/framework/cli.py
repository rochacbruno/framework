import os
from pathlib import Path
from tempfile import TemporaryDirectory

from copier import run_copy, run_update
from cyclopts import App
from git import Repo
from pydantic import BaseModel

app = App(
    name="Framework",
    help="Framework for building Django applications",
)

REPO = os.getenv("FRAMEWORK_REPO", "https://github.com/rochacbruno/framework")


class Context(BaseModel):
    project_template: str = REPO
    app_template: str | Path

    @classmethod
    def build(cls):
        # This local clone is used only once to bootstrap each app
        temp_dir = TemporaryDirectory()
        base_cache_path = Path(temp_dir.name)
        Repo.clone_from(REPO, base_cache_path)
        print(f"Cloned {REPO} to {base_cache_path}")
        app_template = base_cache_path / "templates/app"
        return cls(app_template=app_template)


@app.command
def init(
    destination: Path | None = None,
    project: str = "project",
    apps: list[str] = ["app"],
):
    """Initialize a new application.

    1. Create new project from project_template
    2. Create new apps from app_template
    """
    destination = destination or Path.cwd()
    # Destination must be a valid git repo
    if not destination.exists():
        destination.mkdir(parents=True, exist_ok=True)
        Repo.init(str(destination))

    ctx = Context.build()
    print(ctx)
    print(f"Initializing your project on {destination}")
    run_copy(
        ctx.project_template,
        destination,
        data={
            "project_name": project,
            "template": "project",
        },
    )
    print("Main project created.")

    # for app_name in apps:
    #     run_copy(str(ctx.app_template), destination / app_name)
    #     print(f"Created app {app_name}")


@app.command
def update(destination: Path | None = None):
    """Update an existing application"""
    destination = destination or Path.cwd()
    print(f"Updating your app on {destination}")
    run_update(destination)


@app.command
def validate(destination: Path | None = None):
    """Validate an existing application"""
    destination = destination or Path.cwd()

    print(f"Validating your app on {destination}")


@app.command
def completions():
    """generate shell completions."""
    print(app.generate_completion())
