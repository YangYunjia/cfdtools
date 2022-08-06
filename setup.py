from setuptools import setup, find_packages
from cfdtools import __name__, __version__

with open('readme.md') as f:
      LONG_DESCRIPTION = f.read()

setup(name=__name__,
      version=__version__,
      description='python interface for commercial software CFD++ and Tecplot',
      long_description=LONG_DESCRIPTION,
      long_description_content_type="text/markdown",
      keywords=['CFD', 'machine learning'],
      # download_url='https://github.com/swayli94/cfdpost/',
      license="GPLv3+",
      platforms=["Windows", "Linux"],
      author='Aerolab',
      author_email='yyj980401@126.com',
      packages=find_packages(exclude=["test*"]),
      install_requires=['numpy'],
      classifiers=[
            'Programming Language :: Python :: 3',
            'Topic :: Scientific/Engineering :: Physics',
            'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)'
      ]
)
