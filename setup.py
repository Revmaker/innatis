from setuptools import setup

install_requires = [
    "scikit-learn==0.20.2",
    "scipy==1.2.0",
    "sklearn-crfsuite==0.3.6",
    "tensorflow==2.5.3",
    "word2number==1.1",
    "rasa_nlu==0.14.3",
    "tensorflow-hub==0.2.0",
    "spacy==2.0.18",
    "editdistance~=0.5.2",
]

setup(
    name='innatis',
    install_requires=install_requires,
    packages=['innatis', 'innatis.classifiers', 'innatis.classifiers.bert',
              'innatis.featurizers', 'innatis.extractors'],
    version='0.6.0',
    description='A library of useful custom Rasa components',
    author='CarLabs',
    author_email='blake@carlabs.com',
    url='https://github.com/Revmaker/innatis',
    download_url='https://github.com/Revmaker/innatis/tarball/0.1',
    keywords=['rasa', 'nlu', 'components'],
    classifiers=[]
)
