from pathlib import Path

from copier import run_copy, run_update
from cyclopts import App
from git import Repo
from pydantic import BaseModel

app = App(
    name="Framework",
    help="Framework for building Django applications",
)


class Context(BaseModel):
    project_template: Path = Path()
    app_template: Path = Path()

    @classmethod
    def build(cls):
        if Path("templates").exists():
            return cls(
                project_template=Path("templates/project"),
                app_template=Path("templates/app"),
            )
        base_cache_path = Path("/tmp/framework_cache")
        if not base_cache_path.exists():
            Repo.clone_from(
                "https://github.com/rochacbruno/framework.git", base_cache_path
            )
        project_template = base_cache_path / "templates/project"
        app_template = base_cache_path / "templates/app"
        return cls(project_template=project_template, app_template=app_template)


@app.command
def init(destination: Path | None = None, apps: list[str] = ["app"]):
    """Initialize a new application.

    1. Create new project from project_template
    2. Create new apps from app_template
    """
    destination = destination or Path.cwd()
    ctx = Context.build()
    print(f"Initializing your project on {destination}")
    run_copy(str(ctx.project_template), destination)
    print("Main project created.")

    for app_name in apps:
        run_copy(str(ctx.app_template), destination / app_name)
        print(f"Created app {app_name}")


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
