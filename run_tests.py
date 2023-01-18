import os
import shutil
import subprocess
import pytest
import shutil

src = os.path.join(os.getcwd(), "BlackBoxr")
dst = os.path.join(os.getcwd(), "Test\\BlackBoxr")

shutil.copytree(src, dst)
#os.system('cp -r {} {}'.format(src, dst))

subprocess.run("pytest -n auto --disable-warnings -s -l -v -ra --tb=long", shell=True)

shutil.rmtree(dst)