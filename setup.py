from setuptools import setup

with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()


setup(name='meep_adjoint',
      version='0.1',
      python_requires='>3.7',
      description='Adjoint-solver module for MEEP',
      long_description=readme,
      author='Homer Reid',
      author_email='homer@homerreid.com',
      url='http://github.com/homerreid/meep_adjoint',
      license=license
      packages=['meep_adjoint'])
