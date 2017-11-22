from setuptools import setup, find_packages


setup(
    name='mana_cost',
    version='0.1',
    description='Library for comparing MTG mana costs',
    author='Nick Beeuwsaert',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.6',
        'License :: OSI Approved :: MIT License',
    ],
    packages=find_packages(
        where='src'
    ),
    package_dir={
        '': 'src'
    },
    extras_require={
        'test': [
            'pytest'
        ]
    }
)
