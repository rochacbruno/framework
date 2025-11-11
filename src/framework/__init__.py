from pathlib import Path

from copier import run_copy, run_update
from cyclopts import App

app = App(
    name="Framework",
    help="Framework for building Django applications",
)

source = "templates/django-app"

if not Path(source).exists:
    source = "gh:rochacbruno/framework"


@app.command
def init(destination: Path | None = None):
    """Initialize a new application"""
    destination = destination or Path.cwd()
    print(f"Initializing your app on {destination}")
    run_copy(source, destination)


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


def main() -> None:
    app()
