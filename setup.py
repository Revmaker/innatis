import os

from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

with open(os.path.join(here, "VERSION"), encoding="utf-8") as f:
    __version__ = f.read().strip()

install_requires = [
    "scikit-learn==0.20.2",
    "scipy==1.2.0",
    "sklearn-crfsuite==0.3.6",
    "tensorflow==1.12.2",
    "word2number==1.1",
    "rasa_nlu==0.14.3",
    "tensorflow-hub==0.2.0",
    "spacy==2.0.18",
    "editdistance~=0.5.2",
]

setup(
    name='innatis',
    install_requires=install_requires,
    packages=[
        'innatis',
        'innatis.classifiers',
        'innatis.classifiers.bert',
        'innatis.featurizers',
        'innatis.extractors'
    ],
    version=__version__,
    description='A library of useful custom Rasa components',
    license='Apache License 2.0',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='CarLabs',
    author_email='blake@carlabs.com',
    url='https://github.com/Revmaker/innatis',
    keywords=['rasa', 'nlu', 'components'],
    python_requires=">=3.5",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Text Processing :: Linguistic",
    ]
)
