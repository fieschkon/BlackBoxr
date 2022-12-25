from distutils.core import setup
import setuptools

setup(
  name = 'BlackBoxr',
  packages = setuptools.find_packages(),
  version = '0.0.1',
  license='MIT',
  description = 'System Design Tool',
  long_description = open('README.md').read(),
  long_description_content_type = 'text/markdown',
  author = 'Max Fieschko',
  author_email = 'mfieschko@gmail.com',
  url = '',
  keywords = ['Systems Engineering', 'Requirements', 'Flowchart', 'Block Diagram'],
  install_requires=[],
  classifiers=[
    'Development Status :: 3 - Alpha',      # "3 - Alpha", "4 - Beta" or "5 - Production/Stable"
    'Intended Audience :: Developers',
    'Topic :: Scientific/Engineering :: Visualization',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3.10'
  ],
  project_urls = {

  },
  python_requires='>=3.10'
)