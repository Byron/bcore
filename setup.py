#!/usr/bin/env python
from setuptools import setup, find_packages

pkg_root = 'src/python'

setup(name='bcore',
      version='0.1.0',
      description='The bcore project is designed to help writing powerful and maintainable application rapidly.',
      author='Sebastian Thiel',
      author_email='byronimo@gmail.com',
      url='https://github.com/Byron/bcore',
      packages=find_packages(pkg_root),
      package_dir={'' : pkg_root},
      package_data={'' : ["*.zip"]}
     )
