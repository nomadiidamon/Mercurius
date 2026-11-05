"""Reads shared metadata from ../project.ini (the single source of truth)."""
import configparser
import re
import shutil
from pathlib import Path

from setuptools import setup

HERE = Path(__file__).resolve().parent
REPO_INI = HERE.parent / "project.ini"
LOCAL_INI = HERE / "project.ini"

# An sdist has no parent repo, so ship a copy of project.ini alongside setup.py.
if REPO_INI.is_file():
    shutil.copyfile(REPO_INI, LOCAL_INI)
if not LOCAL_INI.is_file():
    raise FileNotFoundError(f"project.ini not found at {REPO_INI} or {LOCAL_INI}")

cfg = configparser.ConfigParser()
with open(LOCAL_INI, encoding="utf-8-sig") as ini:
    cfg.read_file(ini)
project = cfg["project"]

people = [p.strip() for p in cfg["contributors"]["maintainers"].split(",") if p.strip()]
# "Name (handle) <email>" -> "Name (handle)"
names = [re.sub(r"\s*<.*>$", "", p) for p in people]
emails = [m.group(1) for p in people if (m := re.search(r"<(.*)>$", p))]

setup(
    version=project["version"],
    description=project["description"].strip('"'),
    long_description=(HERE / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    license=project["license"],
    python_requires=cfg["compatibility"]["python_requires"],
    author=", ".join(names),
    author_email=", ".join(emails) or None,
    project_urls={"Homepage": project["homepage"]},
)
