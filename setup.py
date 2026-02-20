from setuptools import setup

def readme():
    with open('README.md') as f:
        return f.read()[309:]

setup(name='dankcli_lib',
      version='0.5.9',
      description='Patched CLI Meme Generator to automatically add whitespace and text to top and bottom',
      long_description=readme(),
      long_description_content_type='text/markdown',
      keywords='dankcli dank meme memegenerator memes generator pillow dankmemes dankcli-lib caption maker make',
      url='https://github.com/TheMrRedSlime/dankcli',
      author='TheMrRedSlime',
      #author_email='',
      license='MIT',
      packages=['dankcli_lib'],
      install_requires=[
          'pillow',
      ],
      package_data={
        'dankcli_lib': ['fonts/*.ttf'],
      },
      zip_safe=False)