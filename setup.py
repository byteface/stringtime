from setuptools import setup, find_packages

with open("README.md", "r") as f:
    long_description = f.read()

from stringtime import __version__
version = __version__

setup(
  name='stringtime',
  version=version,
  author="@byteface",
  author_email="byteface@gmail.com",
  license="MIT",
  url='https://github.com/byteface/stringtime',
  download_url='https://github.com/byteface/stringtime/archive/' + version + '.tar.gz',
  description='Create dates from natural language expressions',
  long_description=long_description,
  long_description_content_type="text/markdown",
  keywords=['date', 'natural language', 'time'],
  python_requires='>=3.6',
  classifiers=[
      "Programming Language :: Python :: 3",
      "Programming Language :: Python",
      "Programming Language :: Python :: 3.7",
      "Programming Language :: Python :: 3.8",
      "Programming Language :: Python :: 3.9",
      "Programming Language :: Python :: 3.10",
      "Development Status :: 4 - Beta",
      "Intended Audience :: Developers",
      "Intended Audience :: Other Audience",
      "License :: OSI Approved :: MIT License",
      "Operating System :: OS Independent",
      "Topic :: Software Development",
      "Topic :: Terminals",
      "Topic :: Utilities",
      'Topic :: Software Development :: Libraries :: Python Modules',
  ],
  install_requires=[
      'python-dateutil==2.8.2',
      'ply==3.11',
  ],
  packages=find_packages(),
  include_package_data=True,
  entry_points={
      'console_scripts': [
          'stringtime = stringtime.__main__:run',
      ],
  },

)
