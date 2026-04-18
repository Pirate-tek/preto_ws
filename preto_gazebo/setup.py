import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'preto_gazebo'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')), #launch executable
        (os.path.join('share', package_name, 'world'), glob('world/*')), #world executable
        (os.path.join('share', package_name, 'config'), glob('config/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='pirate',
    maintainer_email='guruprasath.a003@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'lidar_fusion_node = preto_gazebo.lidar_fusion_node:main'
        ],
    },
)
