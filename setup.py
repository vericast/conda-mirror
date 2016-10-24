from setuptools import setup
import conda_mirror

setup(
    name='conda_mirror',
    author="Eric Dill",
    py_modules=['conda_mirror'],
    version=conda_mirror.__version__,
    author_email='eric.dill@maxpoint.com',
    description='mirror an upstream conda channel to a local directory',
    url='https://github.com/ericdill/conda-mirror',
    platforms='Cross platform (Linux, Mac OSX, Windows)',
    license='BSD 3-Clause',
    install_requires=[
        'requests',
        'tqdm'
    ]
)