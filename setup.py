from setuptools import setup, find_packages

import metaTED


setup(
    name='metaTED',
    version=metaTED.__version__,
    url='https://gitlab.com/petar.maric/metated',
    download_url='http://pypi.python.org/pypi/metaTED',
    license='BSD',
    author='Petar Maric',
    author_email='petar.maric@gmail.com',
    description='Creates metalink files of TED talks for easier downloading',
    long_description=open('README.rst').read(),
    zip_safe=False,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
        'Topic :: Utilities',
    ],
    keywords='TED metalink download video',
    platforms='any',
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts': ['metaTED=metaTED:main']
    },
    install_requires=open('requirements.txt').read().splitlines()
)
