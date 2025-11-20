import io
import os
from contextlib import redirect_stderr
from pathlib import Path
from typing import Annotated

from copier import run_copy, run_update, run_recopy
from cyclopts import App, Parameter
from git import Repo
from yaml import safe_load


app = App(
    name="platform-service-framework",
    help="Framework for building Django applications",
)


def get_repo() -> str:
    """Get the repository URL from environment or use default."""
    return os.getenv(
        "FRAMEWORK_REPO", "https://github.com/ansible/platform-service-framework"
    )


@app.command
def init(
    destination: Path | None = None,
    project: Annotated[str | None, Parameter(alias="-p")] = None,
    apps: Annotated[list[str], Parameter(consume_multiple=True)] = ["api"],
    vcs_ref: Annotated[str | None, Parameter(alias="-r")] = "HEAD",
):
    """Initialize a new Django Project.

    ## Examples
    ```bash
    # New project on current folder with one app named api:
    platform-service-framework init
    # New project on specific folder with one app named api:
    platform-service-framework init /tmp/foo
    # New project on named folder with 3 apps:
    platform-service-framework init my-service --apps api web core

    ```
    ---
    Args:
        destination: The root of the repository
        project: project name [default to destination folder name]
        apps: names for each app to be initialized
        vcs_ref: VCS reference to use for the template [default to HEAD]
    """
    destination = destination or Path.cwd()
    project = project or destination.name.replace("-", "_")
    if not destination.exists():
        destination.mkdir(parents=True, exist_ok=True)
    if not Path(destination / ".git").exists():
        Repo.init(str(destination), initial_branch="devel")

    print(f"Initializing your project on {destination}")
    run_copy(
        get_repo(),
        destination,
        data={
            "project_name": project,
            "template": "templates/project",
        },
        vcs_ref=vcs_ref,
    )
    print("Main project created.")

    apps_destination = destination / "apps"
    for app_name in apps:
        run_copy(
            get_repo(),
            apps_destination / app_name,
            data={
                "project_name": project,
                "template": "templates/app",
            },
            vcs_ref=vcs_ref,
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
def update(
    destination: Path | None = None,
    vcs_ref: Annotated[str | None, Parameter(alias="-r")] = "HEAD",
):
    """Update an existing application.

    ## Examples
    ```bash
    # Update project to latest devel branch:
    platform-service-framework update
    # Update project to specific VCS reference:
    platform-service-framework update -r f46e071
    ```
    ---
    Args:
        destination: The root of the repository
        vcs_ref: VCS reference to use for the template [default to HEAD]
    """
    destination = destination or Path.cwd()
    print(f"Updating your app on {destination}")
    if not Path(destination / ".git").exists():
        print(
            "Updating is only supported in git-tracked repositories. Please initialize your repository."
        )
        return False
    repo = Repo(destination)
    if repo.is_dirty():
        print(
            f"There are uncommitted changes in {destination}, please commit or stash them first"
        )
        return False
    run_update(
        src_path=get_repo(),
        dst_path=destination,
        overwrite=True,
        skip_answered=True,
        vcs_ref=vcs_ref,
    )


@app.command
def validate(
    destination: Path | None = None,
    vcs_ref: Annotated[str | None, Parameter(alias="-r")] = "HEAD",
) -> bool:
    """Validate an existing application

    ## Examples
    ```bash
    # Validate template to latest HEAD branch:
    platform-service-framework validate
    # Update project to specific VCS reference:
    platform-service-framework validate -r f46e071
    ```
    ---
    Args:
        destination: The root of the repository
        vcs_ref: VCS reference to use for the template [default to HEAD]
    """
    destination = destination or Path.cwd()
    print(f"Validating your app on {destination}")
    answers_path = destination / ".copier-answers.yml"
    if not answers_path.exists():
        print(
            "No answers file found (.copier-answers.yml), please run the command from the root of the project"
        )
        return False
    # Run test copier "recopy" to retrieve possible conflicts
    f = io.StringIO()
    with redirect_stderr(f):
        run_recopy(
            src_path=get_repo(),
            dst_path=destination,
            skip_answered=True,
            overwrite=True,
            vcs_ref=vcs_ref,
            pretend=True,
        )
    output = f.getvalue().splitlines()
    # Read protected files defined under the framework config
    config_path = destination / ".protected_files.yaml"
    config = safe_load(config_path.read_text())
    protected_files = config["protected_files"]
    # Retrieve conflicts and compare them to the list of protected files
    conflicts = [line for line in output if "conflict" in line or "create" in line]
    infractions = list(
        {
            conflict
            for conflict in conflicts
            for file in protected_files
            if file in conflict
        }
    )
    if infractions:
        print("✗ The following files should not be modified or deleted: ✗")
        print("\n".join(f"{i}" for i in infractions))
        print("✗ Please undo these changes and run the command again ✗")
        return False
    else:
        print(
            "✓ No framework infractions found, your project is ready to be updated! ✓"
        )
        return True


@app.command
def completions():
    """generate shell completions."""
    print(app.generate_completion())
