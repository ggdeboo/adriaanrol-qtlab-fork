from setuptools import setup, find_packages

setup(name='qtlab',
      version='0.4.0',
      description='Python based measurement environment',
      url='https://github.com/AdriaanRol/test_pip_installer',
      packages=find_packages(),
      entry_points={'console_scripts': ['qtlab = qtlab.__main__:main']},
      license='GNU General Public License 2',)
