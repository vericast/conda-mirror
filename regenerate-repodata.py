import subprocess
import os
import sys
import tempfile
import shutil
import glob


REPO_NAME = "local-repo"
if os.path.exists(REPO_NAME):
    shutil.rmtree(REPO_NAME)

CONDA_BLD_PATH = tempfile.TemporaryDirectory().name
os.environ["CONDA_BLD_PATH"] = CONDA_BLD_PATH

BITS = 64
if sys.maxsize <= 2**32:
    BITS = 32
if sys.platform == "darwin":
    CONDA_PLATFORM = 'osx-64'
elif 'win' in sys.platform:
    CONDA_PLATFORM = 'win-%s' % BITS
elif sys.platform == 'linux':
    CONDA_PLATFORM = 'linux-%s' % BITS
else:
    raise NotImplementedError("Generating a conda repo is not implemented for "
                              "your platform: %s-%s" % (sys.platform, BITS))

if not os.path.exists(REPO_NAME):
    os.mkdir(REPO_NAME)

for channel in ('linux-64', 'linux-32', 'win-32', 'win-64', 'osx-64'):
    path = os.path.join(REPO_NAME, channel)
    if not os.path.exists(path):
        os.mkdir(path)

for recipe in ('a', 'b'):
    subprocess.check_call(('conda build test/recipes/%s' % recipe).split(),
                          env=os.environ)

copy_from = os.path.join(CONDA_BLD_PATH, CONDA_PLATFORM, "*.tar.bz2")
copy_to = os.path.join(REPO_NAME, CONDA_PLATFORM)
for f in glob.glob(os.path.join(CONDA_BLD_PATH, CONDA_PLATFORM, "*.tar.bz2")):
    shutil.copy(f, copy_to)
    subprocess.check_call(('conda convert -p all %s' % os.path.join(
        CONDA_PLATFORM, os.path.basename(f))).split(), cwd=REPO_NAME)

for folder in os.listdir(REPO_NAME):
    full_path = os.path.join(REPO_NAME, folder)
    if os.path.isdir(full_path):
        subprocess.check_call(('conda index %s' % full_path).split())
