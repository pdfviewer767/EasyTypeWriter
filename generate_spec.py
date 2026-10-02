import shutil
from pathlib import Path


def generate_spec(destination=None):
    project_root = Path(__file__).resolve().parent
    destination = Path(destination) if destination else project_root / "main.spec"
    shutil.copyfile(project_root / "build.spec", destination)
    return destination


if __name__ == "__main__":
    print(f"Created {generate_spec()}")
