import io
import os
import sys
from contextlib import redirect_stderr
from importlib.metadata import distribution
from pathlib import Path
from typing import Annotated

import yaml
from copier import run_copy, run_recopy, run_update
from cyclopts import App, Parameter
from git import Repo
from yaml import safe_load

from .utils import get_repo


app = App(
    name="platform-service-framework",
    help="Framework for building Django applications",
)


@app.command
def init(
    destination: Path | None = None,
    project: Annotated[str | None, Parameter(alias="-p")] = None,
    apps: Annotated[list[str], Parameter(consume_multiple=True)] = ["api"],
):
    """Initialize a new Django Project.

    The template version is automatically detected based on how the CLI was installed.

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
    """
    destination = destination or Path.cwd()
    project = project or destination.name.replace("-", "_")
    if not destination.exists():
        destination.mkdir(parents=True, exist_ok=True)
    if not Path(destination / ".git").exists():
        Repo.init(str(destination), initial_branch="devel")

    print(f"Initializing your project on {destination}")
    src_path, vcs_ref = get_repo()
    run_copy(
        src_path,
        destination,
        vcs_ref=vcs_ref,
        data={
            "project_name": project,
            "template": "templates/project",
        },
    )
    print("Main project created.")

    apps_destination = destination / "apps"
    for app_name in apps:
        run_copy(
            src_path,
            apps_destination / app_name,
            vcs_ref=vcs_ref,
            data={
                "project_name": project,
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

    # Initial commit
    try:
        repo = Repo(destination)
        if repo.is_dirty(untracked_files=True):
            print("\nCommitting initial project...")
            repo.git.add(A=True)

            # Build detailed commit message
            commit_msg = f"""[platform-service-framework] Initialize project

Project: {project}
Apps: {", ".join(apps) if apps else "none"}
Template source: {src_path}
Template version: {vcs_ref or "HEAD"}
"""
            repo.index.commit(commit_msg)
            print("✓ Initial commit created")
        else:
            print("\nNo changes to commit")
    except Exception as e:
        print(f"\nNote: Could not create initial commit: {e}")
        print("You may want to commit manually with: git add -A && git commit")


@app.command
def update(
    destination: Path | None = None,
):
    """Update an existing application.

    The template version is automatically detected based on how the CLI was installed.

    ## Examples
    ```bash
    # Update project to detected template version:
    platform-service-framework update
    ```
    ---
    Args:
        destination: The root of the repository
    """
    destination = destination or Path.cwd()
    print(f"Updating your app on {destination}")

    # Check working tree is clean (unique to update, not needed for validate)
    if Path(destination / ".git").exists():
        try:
            repo = Repo(destination)
            if repo.is_dirty(untracked_files=True):
                print("Error: Working tree has uncommitted changes.")
                print("Please commit or stash your changes before running update.")
                sys.exit(1)
            print("Working tree is clean")
        except Exception as e:
            print(f"Error: Could not check git status: {e}")
            sys.exit(1)

    # Validate before making any changes (checks git repo and copier answers)
    if not validate(destination):
        print("\nValidation failed. Please fix the issues before updating.")
        sys.exit(1)

    # Detect current framework source
    src_path, vcs_ref = get_repo()

    # Read current copier answers
    answers_file = destination / ".copier-answers.yml"
    with open(answers_file) as f:
        answers = yaml.safe_load(f)

    old_src = answers.get("_src_path")
    print(f"Current template source: {old_src}")
    print(f"Detected framework source: {src_path}")

    # Update source in answers if changed
    source_changed = old_src != src_path
    if source_changed:
        print(f"Updating template source to: {src_path}")
        answers["_src_path"] = src_path

        # Write updated answers
        with open(answers_file, "w") as f:
            f.write(
                "# Changes here will be overwritten by Copier; NEVER EDIT MANUALLY\n"
            )
            yaml.dump(answers, f, default_flow_style=False, sort_keys=False)

        print("✓ Updated .copier-answers.yml")

        # Commit the source change
        try:
            repo.git.add(str(answers_file))
            commit_msg = f"""[platform-service-framework] Update template source

Old source: {old_src}
New source: {src_path}
Template version: {vcs_ref or "HEAD"}

This commit updates .copier-answers.yml to point to the new template source.
"""
            repo.index.commit(commit_msg)
            print("✓ Committed .copier-answers.yml changes")
        except Exception as e:
            print(f"Warning: Could not commit .copier-answers.yml: {e}")
    else:
        print("Template source unchanged")

    # Run copier update
    print("\nRunning copier update...")
    if vcs_ref:
        print(f"Using VCS ref: {vcs_ref}")

    run_update(
        destination,
        vcs_ref=vcs_ref,
        overwrite=True,
        skip_answered=True,
    )

    # Auto-commit if successful, error if conflicts
    try:
        repo = Repo(destination)

        # Check for merge conflicts
        if repo.index.unmerged_blobs():
            print("\nError: Merge conflicts detected during update.")
            print("Please resolve conflicts manually and commit the changes.")
            print("\nTo see conflicts:")
            print("  git status")
            sys.exit(1)

        # Check if there are changes to commit
        if repo.is_dirty(untracked_files=True):
            print("\nCommitting update changes...")
            repo.git.add(A=True)

            commit_msg = f"""[platform-service-framework] Update project from template

Template source: {src_path}
Template version: {vcs_ref or "HEAD"}

This commit applies updates from the template.
"""
            repo.index.commit(commit_msg)
            print("✓ Update committed successfully")
        else:
            print("\nNo changes from update")

    except Exception as e:
        print(f"\nError: Could not commit update: {e}")
        print("Please review and commit changes manually.")
        sys.exit(1)


@app.command
def validate(
    destination: Path | None = None,
) -> bool:
    """Validate an existing application against the detected template version.

    The template version is automatically detected based on how the CLI was installed.

    ## Examples
    ```bash
    # Validate project against detected template:
    platform-service-framework validate
    ```
    ---
    Args:
        destination: The root of the repository
    """
    destination = destination or Path.cwd()
    print(f"Validating your app on {destination}")

    # Check if it's a git repository
    if not Path(destination / ".git").exists():
        print(
            "Platform service framework is only supported in git-tracked repositories. Please initialize your repository."
        )
        return False

    # Check if it's a copier project
    if not Path(destination / ".copier-answers.yml").exists():
        print(
            "No answers file found (.copier-answers.yml), please run the command from the root of the project"
        )
        return False

    copier_answers = safe_load((destination / ".copier-answers.yml").read_text())

    # try to read _commit from answer if it doesnt exist return false
    if "_commit" not in copier_answers:
        print(
            "Error: .copier-answers.yml is missing the '_commit' key. Cannot validate project."
        )
        return False

    # Run test copier "recopy" to retrieve possible conflicts
    src_path, _ = get_repo()
    f = io.StringIO()
    with redirect_stderr(f):
        run_recopy(
            src_path=src_path,
            dst_path=destination,
            skip_answered=True,
            overwrite=True,
            vcs_ref=copier_answers.get("_commit"),
            pretend=True,
        )
    output = f.getvalue().splitlines()
    # Read protected files defined under the framework config
    config_path = destination / ".protected_files.yaml"
    if not config_path.exists():
        print("Note: .protected_files.yaml not found. Skipping protected files check.")
        print(
            "✓ No framework infractions found, your project is ready to be updated! ✓"
        )
        return True

    try:
        config = safe_load(config_path.read_text())
        if not config or "protected_files" not in config:
            print(f"Error: {config_path} is missing 'protected_files' key.")
            return False
        protected_files = config["protected_files"]
    except Exception as e:
        print(f"Error: Failed to parse {config_path}: {e}")
        return False

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


@app.command
def debug():
    """Show debug information about the framework installation."""
    src_path, vcs_ref = get_repo()
    print(f"Template source: {src_path}")
    if vcs_ref:
        print(f"VCS ref: {vcs_ref}")

    # Show additional debug info if FRAMEWORK_DEBUG is set
    if os.getenv("FRAMEWORK_DEBUG"):
        try:
            dist = distribution("platform-service-framework")
            print(f"\nPackage version: {dist.version}")
            print(f"Package location: {dist._path}")  # type: ignore

            if dist._path:  # type: ignore
                direct_url_file = dist._path / "direct_url.json"  # type: ignore
                if direct_url_file.exists():
                    print("\nDirect URL metadata:")
                    print(direct_url_file.read_text())
        except Exception as e:
            print(f"\nError getting debug info: {e}")
