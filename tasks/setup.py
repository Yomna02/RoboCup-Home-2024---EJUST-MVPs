import os
from glob import glob
from setuptools import setup

package_name = 'tasks'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='beedo',
    maintainer_email='abdallah.amr@ejust.edu.eg',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'curry_luggage=tasks.curry_my_luggage:main',
            'battery=tasks.pub_battery:main',
            'navigator=tasks.navigator:main',
            'mates=tasks.find_mates:main',
            'receptionist=tasks.receptionist:main',
            'gui=tasks.gui:main',
            "presentation=tasks.presentation:main",
        ],
    },
)
