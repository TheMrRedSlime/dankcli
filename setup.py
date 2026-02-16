from setuptools import setup

def readme():
    with open('README.md') as f:
        return f.read()[309:]

setup(name='dankcli-lib',
      version='0.5.9',
      description='Patched CLI Meme Generator to automatically add whitespace and text to top',
      long_description=readme(),
      long_description_content_type='text/markdown',
      keywords='dankcli dank meme memegenerator memes generator pillow dankmemes damkcli-lib caption maker make',
      url='https://github.com/',
      author='TheMrRedSlime',
      #author_email='',
      license='MIT',
      packages=['dankcli-lib'],
      install_requires=[
          'pillow',
      ],
      package_data={
        'dankcli-lib': ['fonts/*.ttf'],
      },
      zip_safe=False)