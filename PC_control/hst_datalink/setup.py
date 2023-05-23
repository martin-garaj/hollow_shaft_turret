from setuptools import setup, find_packages

setup(
    name='hst_datalink',
    version='0.1.0',
    author='Martin Garaj',
    author_email='garaj.martin@gmail.com',
    description='Library for Hollow Shaft Turret datalink',
    long_description=open('README.md', 'r').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/library',
    packages=find_packages(),
    install_requires=open('requirements.txt', 'r').read().splitlines(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)