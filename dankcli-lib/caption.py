from PIL import Image, ImageFont, ImageDraw
import math

class Caption:
    """Handles image captioning with text overlay."""
    
    # Default styling constants
    TOP_PADDING = 10
    BOTTOM_PADDING = 10
    WIDTH_PADDING = 10
    MINIMUM_FONT_SIZE = 13
    HW_ASPECT_RATIO_THRESHOLD = 1.666
    
    def __init__(self, image_path, text, font_path="arial.ttf", separator_line=False, 
                 bottom_text=None, top_font_color=None, bottom_font_color=None):
        """
        Initialize Caption with an image and text.
        
        Args:
            image_path: Path to the source image
            text: Caption text (supports \\n for newlines)
            font_path: Path to font file (defaults to arial.ttf)
            separator_line: Whether to draw a black line between text and image
            bottom_text: Optional text to place at the bottom of the image
            top_font_color: Font color for top text (defaults to black (0,0,0) if None)
            bottom_font_color: Font color for bottom text (defaults to white (255,255,255) if None)
        """
        self.image = Image.open(image_path)
        self.text = text.replace("\\n", "\n")
        self.bottom_text = bottom_text.replace("\\n", "\n") if bottom_text else None
        self.font_path = font_path
        self.separator_line = separator_line
        self.width, self.height = self.image.size
        
        # Set default colors if not provided
        self.top_font_color = top_font_color if top_font_color is not None else (0, 0, 0)
        self.bottom_font_color = bottom_font_color if bottom_font_color is not None else (255, 255, 255)
        
        # Initialize font
        try:
            font_size = self._calculate_font_size()
            self.font = ImageFont.truetype(font_path, size=font_size)
        except OSError:
            self.font = ImageFont.load_default()
    
    def _calculate_font_size(self):
        """Calculate appropriate font size based on image dimensions."""
        temp_size = max(math.floor(self.height / 13), self.MINIMUM_FONT_SIZE)
        
        # Scale down for very tall images
        if self.height / self.width >= self.HW_ASPECT_RATIO_THRESHOLD:
            return math.floor(temp_size / 1.5)
        return temp_size
    
    def _get_text_dimensions(self, text):
        """Get width and height of text with current font."""
        bbox = self.font.getbbox(text)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    
    def _wrap_text(self, text, max_width):
        """Wrap text to fit within max_width."""
        lines = []
        words = text.split(' ')
        i = 0
        
        while i < len(words):
            line = ''
            while (i < len(words) and 
                   self._get_text_dimensions(line + words[i])[0] < max_width - self.WIDTH_PADDING):
                line = line + words[i] + " "
                i += 1
            
            if not line:
                line = words[i]
                i += 1
            
            lines.append(line.strip())
        
        return '\n'.join(lines)
    
    def _process_text(self):
        """Process and wrap text for rendering."""
        # Wrap each intentional newline section individually
        wrapped_lines = "\n".join([
            self._wrap_text(line, self.width) 
            for line in self.text.split("\n")
        ])
        return wrapped_lines
    
    def _calculate_text_height(self, text):
        """Calculate total height needed for text."""
        line_list = text.split('\n')
        if not line_list:
            return 0
        
        _, line_height = self._get_text_dimensions(line_list[0])
        # Add spacing between lines (roughly 20% of line height)
        total_text_height = len(line_list) * (line_height * 1.2)
        return int(total_text_height + self.TOP_PADDING + self.BOTTOM_PADDING)
    
    def _get_text_position(self, text):
        """Calculate top-left corner position for centered text."""
        line_list = text.split('\n')
        # Find width of the widest line for centering
        max_w = max(self._get_text_dimensions(line)[0] for line in line_list)
        return ((self.width - max_w) / 2, self.TOP_PADDING)
    
    def _get_text_position_bottom(self, text, y_offset):
        """Calculate top-left corner position for centered bottom text."""
        line_list = text.split('\n')
        # Find width of the widest line for centering
        max_w = max(self._get_text_dimensions(line)[0] for line in line_list)
        return ((self.width - max_w) / 2, y_offset + self.TOP_PADDING)
    
    def generate(self):
        """
        Generate the captioned image.
        
        Returns:
            PIL.Image: The captioned image
        """
        # Process top text
        wrapped_top_text = self._process_text()
        top_text_height = self._calculate_text_height(wrapped_top_text)
        
        # Process bottom text if provided
        bottom_text_height = 0
        wrapped_bottom_text = None
        if self.bottom_text:
            wrapped_bottom_text = "\n".join([
                self._wrap_text(line, self.width) 
                for line in self.bottom_text.split("\n")
            ])
            bottom_text_height = self._calculate_text_height(wrapped_bottom_text)
        
        # Calculate total canvas height
        total_height = top_text_height + self.height + bottom_text_height
        
        # Create canvas
        canvas = Image.new("RGB", (self.width, total_height), (255, 255, 255))
        
        # Paste the original image in the middle
        canvas.paste(self.image, (0, top_text_height))
        
        # Draw separator line at top if enabled
        if self.separator_line:
            draw = ImageDraw.Draw(canvas)
            # Draw a black line at the bottom of the top white box
            line_y = top_text_height - 1
            draw.line([(0, line_y), (self.width, line_y)], fill=(0, 0, 0), width=2)
        
        # Draw top text
        draw = ImageDraw.Draw(canvas)
        top_text_pos = self._get_text_position(wrapped_top_text)
        
        draw.multiline_text(
            top_text_pos,
            wrapped_top_text,
            fill=self.top_font_color,
            font=self.font,
            align="center",
            spacing=4
        )
        
        # Draw bottom text if provided
        if self.bottom_text and wrapped_bottom_text:
            # Position for bottom text (starts after the image)
            bottom_text_pos = self._get_text_position_bottom(wrapped_bottom_text, top_text_height + self.height)
            
            draw.multiline_text(
                bottom_text_pos,
                wrapped_bottom_text,
                fill=self.bottom_font_color,
                font=self.font,
                align="center",
                spacing=4
            )
            
            # Draw separator line at bottom if enabled
            if self.separator_line:
                line_y = top_text_height + self.height
                draw.line([(0, line_y), (self.width, line_y)], fill=(0, 0, 0), width=2)
        
        return canvas
    
    def save(self, output_path):
        """
        Generate and save the captioned image.
        
        Args:
            output_path: Path to save the output image
        """
        captioned_image = self.generate()
        captioned_image.save(output_path)
        return output_path