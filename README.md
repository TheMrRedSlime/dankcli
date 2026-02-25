# dankcli-lib
[![PyPI version](https://img.shields.io/pypi/v/dankcli-lib.svg?label=PyPI)](https://pypi.org/project/dankcli-lib/)
[![Python Version](https://img.shields.io/badge/Python-3.7%2B-blue.svg)](https://www.python.org/downloads/)
[![Downloads](https://pepy.tech/badge/dankcli-lib)](https://pepy.tech/project/dankcli-lib)

dankcli-lib is a CLI Image Captioning Tool, Meme Generator and Library which automatically adds white space and text to the top of your image.

## Installation

```bash
$ pip install dankcli-lib
```

## Usage

```bash
$ python -m dankcli_lib "path/to/image" "Meme text you want to add" [-f "final_image_name_without_extension"]
```

#### Python:

```python
from dankcli_lib.caption import Caption

caption = Caption("/path/to/image", "Text here", bottom_text="Bottom text here", bottom_font_color="#000000", bottom_text_box=False, separator_line=True, separator_line_color="#000000", top_font_color="#ffffff", top_background_color="#000000", bottom_background_color="#000000", italic=False, bold=False)
caption.save('file.jpg')
```

```python
from dankcli_lib.caption import Caption

with Caption("image.jpg", "Your text") as caption:
    buffer, ext = caption.to_buffer()
    await ctx.send(file=discord.File(buffer, f"image.{ext}"))
```

```python
from dankcli_lib.caption import Caption
import discord

caption = Caption("https://example.com/image.jpg", "Your text")
buffer, ext = caption.to_buffer()
await ctx.send(file=discord.File(buffer, f"image.{ext}"))
caption.close()
```


The text gets automatically wrapped according to width of image but you can also have intentional \n in your text.
The image is saved in the current folder with the name as the current date and time, the name can be changed with the optional `-f` or `--filename` argument, specifying a file name without the file extension. 

## Example

#### Example 1 (showing \n functionality)
```bash
$ python -m dankcli_lib "templates/yesbutno.jpg" "Mom at 2am: Are you awake?\n\nMe:"
```
turns this

![](https://i.imgur.com/nW3XPkF.jpg)

to this

![](https://i.imgur.com/h6qgp9m.png)

#### Example 2 (showing auto textwrap)
```bash
$ python -m dankcli_lib "mymemes/helpmeme.jpg" "When you make a meme generator but now you can't stop making memes"
```
turns this

![](https://i.imgur.com/6CDBFwF.jpg)

to this

![](https://i.imgur.com/lSBUfNb.png)

## Updates


### 0.6.5

Added the discord and discord.py tags

### 0.6.6

Patched URL/Link support caused parsed was undefinied

### 0.6.7

Added GIF SUPPORT!

### 0.6.8

Increased the Font Size

### 0.6.9

Added Compression cause discord's a jerk

### 0.7.0

Added Italic, Bold, Had to Remove all TTF files though.
Bold seems a bit broken rn