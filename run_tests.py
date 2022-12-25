import os
import shutil
import subprocess
import pytest

src = os.path.join(os.getcwd(), "BlackBoxr")
dst = os.path.join(os.getcwd(), "Test/BlackBoxr")

shutil.rmtree(dst)
os.system('cp -r {} {}'.format(src, dst))

subprocess.run("pytest -n auto --disable-warnings -s -l -v -ra --tb=long", shell=True)