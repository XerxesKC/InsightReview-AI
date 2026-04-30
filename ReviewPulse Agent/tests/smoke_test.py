from pathlib import Path


def test_readme_exists() -> None:
    assert Path("README.md").exists()


def test_env_example_exists() -> None:
    assert Path(".env.example").exists()


def test_project_structure_file_exists() -> None:
    assert Path("项目结构.txt").exists()

