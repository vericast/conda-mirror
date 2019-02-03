from setuptools import find_packages, setup
import versioneer

try:
    with open('README.md') as f:
        long_description = f.read()
except:
    long_description = ''
    print('Failed to load README.md as long_description')

setup(
    name='conda_mirror',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    author="Eric Dill",
    packages=find_packages(),
    author_email='eric.dill@maxpoint.com',
    description='Mirror an upstream conda channel to a local directory',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/valassis-digital-media/conda-mirror',
    platforms=['Linux', 'Mac OSX', 'Windows'],
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
