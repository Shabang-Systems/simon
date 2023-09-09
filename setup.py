import os
from glob import glob
from setuptools import setup, find_packages
from pkg_resources import parse_requirements
import pathlib

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

with pathlib.Path(os.path.join(os.path.dirname(__file__),
                               'requirements.txt')).open() as requirements_txt:
    requirements = [str(i) for i in
                    parse_requirements(requirements_txt)]

setup(
    name = "simon-search",
    version = "0.0.1.post4",
    author = "Shabang Systems, LLC",
    author_email = "hello@shabang.io",
    description = "A pipeline which allows for the ingestion, storage, and processing of a large body of textual information with LLMs.",
    packages=find_packages(),
    long_description=read('README.md'),
    entry_points = {
        'console_scripts': ['simon-setup=simon.provision:execute'],
    },
    long_description_content_type='text/markdown',
    extras_require={
        "web": ["Flask==2.3.2", "gunicorn==21.2.0",
                "flask_cors==4.0.0", "Requests==2.31.0"],
        "asr": ["openai-whisper==20230314"]
    },
    include_package_data=True,
    package_data={
        'simon': [os.path.basename(i) for i in glob("simon/*.sql")],
    },
    install_requires=requirements,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "Natural Language :: English",
        "Topic :: Database",
        "Topic :: Scientific/Engineering :: Artificial Intelligence"
    ],
)


