from PIL import Image, ImageFont, ImageDraw
import math
import datetime

TOP_PADDING = 10
BOTTOM_PADDING = 10
MINIMUM_FONT_SIZE = 13
HW_ASPECT_RATIO_THRESHOLD = 1.666
WIDTH_PADDING = 10 

def get_font_size(img):
    width, height = img.size
    temp_size = max(math.floor(height / 13), MINIMUM_FONT_SIZE)
    # Scale down for very tall images to prevent text from taking over
    if height / width >= HW_ASPECT_RATIO_THRESHOLD:
        return math.floor(temp_size / 1.5)
    return temp_size

def get_text_dimensions(text, font):
    # Modern way to get text width/height in Pillow 10+
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

def get_top_left_corner(lines, font, img_width):
    line_list = lines.split('\n')
    # Find width of the widest line for centering
    max_w = max(get_text_dimensions(line, font)[0] for line in line_list)
    return ((img_width - max_w) / 2, TOP_PADDING)

def text_wrap(text, font, max_width):
    lines = []
    words = text.split(' ')
    i = 0
    while i < len(words):
        line = ''
        while i < len(words) and get_text_dimensions(line + words[i], font)[0] < max_width - WIDTH_PADDING:
            line = line + words[i] + " "
            i += 1
        if not line:
            line = words[i]
            i += 1
        lines.append(line.strip())
    return '\n'.join(lines)

def get_white_space_height(lines, font):
    line_list = lines.split('\n')
    if not line_list: return 0
    _, line_height = get_text_dimensions(line_list[0], font)
    # Add spacing between lines (roughly 20% of line height)
    total_text_height = len(line_list) * (line_height * 1.2)
    return int(total_text_height + TOP_PADDING + BOTTOM_PADDING)

def get_file_name():
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S")