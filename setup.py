from setuptools import setup, find_packages
import versioneer

setup(
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    name='conda_mirror',
    author="Eric Dill",
    packages=find_packages(),
    author_email='eric.dill@maxpoint.com',
    description='mirror an upstream conda channel to a local directory',
    url='https://github.com/ericdill/conda-mirror',
    platforms='Cross platform (Linux, Mac OSX, Windows)',
    license='BSD 3-Clause',
    install_requires=[
        'requests',
        'pyyaml',
    ],
    entry_points={
        "console_scripts": [
            'conda-mirror = conda_mirror.conda_mirror:cli'
        ]
    }
)

