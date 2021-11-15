from setuptools import setup

setup(name='django_firebase',
      version='0.1',
      description='A proxy layer between Django ORM and Firebase',
      url='https://github.com/lodlaw/django-firebase',
      author='Anh Pham',
      author_email='anh.pham@lodlaw.com',
      license='MIT',
      packages=['django_firebase'],
      install_requires=[
          'firebase-admin',
          'Django'
      ],
      zip_safe=False)
