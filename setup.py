# -*- coding: utf-8 -*-
import sys


if sys.platform == 'win32':
    from setuptools import setup
    kw = {
        'entry_points': {
            'console_scripts': ['metaTED=metaTED:main']
        },
        'install_requires': open('requirements.txt').read().splitlines()
    }
else:
    from distutils.core import setup
    kw = {'scripts': ['scripts/metaTED']}

setup(
    name='metaTED',
    version=__import__('metaTED').__version__,
    url='http://bitbucket.org/petar/metated/',
    download_url='http://pypi.python.org/pypi/metaTED',
    license='BSD',
    author='Petar Maric',
    author_email='petar.maric@gmail.com',
    description='Creates metalink files of TED talks for easier downloading',
    long_description=open('README').read(),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.5',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
        'Topic :: Utilities',
    ],
    keywords='TED metalink download video',
    platforms='any',
    packages=['metaTED', 'metaTED.crawler'],
    data_files=[('metaTED/templates', ['metaTED/templates/template.metalink'])],
    **kw
)