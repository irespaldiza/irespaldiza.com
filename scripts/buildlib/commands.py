import subprocess

from .paths import ROOT


def run(command):
    subprocess.run(command, cwd=ROOT, check=True)
