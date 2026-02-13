from setuptools import setup

package_name = 'vision'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
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
            'human_pose = vision.human_pose:main',
            'chairs = vision.chairs:main',
            'face_features = vision.face_feat:main',
            'bag = vision.bags:main',
            'person = vision.person:main',
            'detect_face = vision.face_detect:main',
            'recog_face = vision.face_recog:main'
        ],
    },
)
