from setuptools import setup

setup(name='git-fuzzy-bisector',
      version='0.1',
      description='A fuzzy bisector for git',
      url='http://github.com/ggould256/bisector',
      author='Grant Gould',
      author_email='ggould@alum.mit.edu',
      license='MIT',
      packages=['git_fuzzy_bisector'],
      install_requires=[
        'numpy>=1.19.5',
        'scipy>=1.6.0',
        'sparklines',
      ],
    scripts=['bin/git-fuzzy-bisect'],
    zip_safe=False)
