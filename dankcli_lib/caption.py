from PIL import Image, ImageFont, ImageDraw, ImageSequence
import math, io, requests
from urllib.parse import urlparse

class Caption:
    """Handles image captioning with text overlay."""
    
    # Default styling constants
    TOP_PADDING = 10
    BOTTOM_PADDING = 10
    WIDTH_PADDING = 10
    MINIMUM_FONT_SIZE = 24
    HW_ASPECT_RATIO_THRESHOLD = 1.666
    MAX_BOTTOM_TEXT_HEIGHT_RATIO = 0.334

    def __enter__(self):
        """Enter the runtime context for the with statement."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the runtime context and clean up resources."""
        self.close()
    
    def __init__(self, image_path, text, separator_line=False, separator_line_color=None, 
                 bottom_text=None, bottom_text_box=True,
                 top_font_color=None, bottom_font_color=None, top_background_color=None, bottom_background_color=None, italic=False, bold=False):
        """
        Initialize Caption with an image and text.
        
        Args:
            image_path: Path to the source image
            text: Caption text (supports \\n for newlines)
            font_path: Path to font file (defaults to arial.ttf)
            separator_line: Whether to draw a black line between text and image
            bottom_text: Optional text to place at the bottom of the image
            bottom_text_box: If True, adds white box for bottom text. If False, overlays text on image
            top_font_color: Font color for top text (defaults to black (0,0,0) if None)
            bottom_font_color: Font color for bottom text (defaults to white (255,255,255) if None)
            italic: Whether Text should be Italic
            bold: Whether Text should be Bold
        """
        #self.image = Image.open(image_path)
        parsed = urlparse(image_path)
        if parsed.scheme in ('http', 'https'):
            response = requests.get(image_path, stream=True)
            response.raise_for_status()
            self.image = Image.open(io.BytesIO(response.content))
        else:
            self.image = Image.open(image_path)
            
        self.text = text.replace("\\n", "\n")
        self.bottom_text = bottom_text.replace("\\n", "\n") if bottom_text else None
        self.bottom_text_box = bottom_text_box
        self.separator_line = separator_line
        self.italic = italic
        self.bold = bold
        self.separator_line_color = separator_line_color if separator_line_color is not None else (0, 0, 0)

        self.width, self.height = self.image.size
        
        # Set default colors if not provided
        self.top_font_color = top_font_color if top_font_color is not None else (0, 0, 0)
        self.bottom_font_color = bottom_font_color if bottom_font_color is not None else (0, 0, 0)
        
        self.top_background_color = top_background_color if top_background_color is not None else (255, 255, 255)
        self.bottom_background_color = bottom_background_color if bottom_background_color is not None else (255, 255, 255)
        
        # Initialize font
        self.font = ImageFont.load_default()

    def _is_animated_gif(self):
        """Check if the image is an animated GIF."""
        return (hasattr(self.image, 'is_animated') and 
                self.image.is_animated and 
                getattr(self.image, 'format', '') == 'GIF')

    def compress_to_size(self, buffer, target_size=8*1000*1000, original_format=None):
        """Compress image to fit under target size (default 8MB)"""
        # Check current size
        buffer.seek(0, 2)
        current_size = buffer.tell()
        buffer.seek(0)
        
        
        if current_size <= target_size:
            return buffer
        
        # Open image from buffer
        img = Image.open(buffer)
        
        # Determine format
        if original_format:
            format = original_format.upper()
        else:
            format = img.format if img.format else 'JPEG'
        
        
        output = io.BytesIO()
        
        # Handle different formats
        if format == 'GIF':
            return self._compress_gif(img, target_size)
        
        elif format == 'PNG':
            # Convert PNG to JPEG with white background
            return self._convert_png_to_jpeg(img, target_size)
        
        else:  # JPEG and others
            return self._compress_jpeg(img, target_size)

    def _convert_png_to_jpeg(self, img, target_size):
        """Convert PNG to JPEG with white background"""
        
        # Create white background
        if img.mode == 'RGBA':
            # Split alpha
            rgb = Image.new('RGB', img.size, (255, 255, 255))
            rgb.paste(img, mask=img.split()[3])  # Use alpha as mask
            img_rgb = rgb
        elif img.mode == 'P':
            # Convert palette mode
            img_rgb = img.convert('RGB')
        else:
            img_rgb = img.convert('RGB')
        
        # Now compress as JPEG
        return self._compress_jpeg(img_rgb, target_size)

    def _compress_jpeg(self, img, target_size):
        output = io.BytesIO()
        # Ensure RGB
        if img.mode != 'RGB':
            img = img.convert('RGB')

        for quality in [85, 55, 30]: # Fewer steps = faster response
            output.seek(0)
            output.truncate()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            if output.tell() < target_size:
                output.seek(0)
                return output

        # If quality reduction failed, aggressive resize
        scale = 0.7 
        while output.tell() > target_size:
            new_size = (int(img.width * scale), int(img.height * scale))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            output.seek(0)
            output.truncate()
            img.save(output, format='JPEG', quality=50, optimize=True)
            scale -= 0.1
        
        output.seek(0)
        return output

    def _compress_gif(self, img, target_size):
        """Compresses GIF by reducing colors and resolution until it fits target_size."""
        
        # Start with current resolution or cap at 800px
        current_width = min(img.width, 800)
        colors = 256 # Start with max colors
        
        while True:
            scale = current_width / float(img.width)
            new_size = (current_width, int(float(img.height) * scale))
            
            frames = []
            durations = []
            
            for frame in ImageSequence.Iterator(img):
                # 1. Resize
                f = frame.resize(new_size, Image.Resampling.BILINEAR)
                # 2. Reduce Quality (Quantize colors)
                f = f.convert("P", palette=Image.Palette.ADAPTIVE, colors=colors)
                frames.append(f)
                durations.append(frame.info.get('duration', 100))
            
            output = io.BytesIO()
            frames[0].save(
                output, format='GIF', save_all=True, append_images=frames[1:],
                duration=durations, loop=0, optimize=True, disposal=2
            )
            
            output.seek(0, 2)
            final_size = output.tell()
            output.seek(0)
            
            
            # Check if we are under the limit
            if final_size <= target_size:
                return output
            
            # If still too big, get more aggressive
            if colors > 64:
                colors //= 2  # Drop colors first to preserve sharpness
            elif current_width > 200:
                current_width -= 100 # Then drop resolution
            else:
                # If still too big at tiny res/colors, skip frames
                return output

    def generate_gif(self):
        """Generate captioned GIF preserving animation."""
        frames = []
        durations = []
        
        # Process each frame
        for frame in ImageSequence.Iterator(self.image):
            # Convert frame to RGB and copy
            frame_rgb = frame.convert('RGB')
            
            # Temporarily replace self.image with current frame
            original_image = self.image
            original_size = (self.width, self.height)
            
            self.image = frame_rgb
            self.width, self.height = self.image.size
            
            # Generate captioned frame
            captioned_frame = self.generate()
            frames.append(captioned_frame)
            
            # Get frame duration
            try:
                durations.append(frame.info.get('duration', 100))
            except:
                durations.append(100)
        
        # Restore original image
        self.image = original_image
        self.width, self.height = original_size
        
        # Save as animated GIF
        output = io.BytesIO()
        frames[0].save(
            output,
            format='GIF',
            save_all=True,
            append_images=frames[1:],
            duration=durations,
            loop=0,
            disposal=2
        )
        output.seek(0)
        return output
    
    def _draw_text_with_style(self, draw, position, text, fill, align="center", spacing=4):
        """Draw text with bold/italic simulation"""
        x, y = position
        
        if self.bold and self.italic:
            # Bold Italic: draw multiple times with offset + shear
            self._draw_bold_italic_text(draw, position, text, fill, align, spacing+4)
        elif self.bold:
            # Bold: draw text multiple times with slight offset
            offsets = [(0,0), (1,0), (0,1), (1,1)]
            for dx, dy in offsets:
                draw.multiline_text(
                    (x + dx, y + dy),
                    text,
                    fill=fill,
                    font=self.font,
                    align=align,
                    spacing=spacing+4
                )
        elif self.italic:
            # Italic: draw with shear effect
            self._draw_italic_text(draw, position, text, fill, align, spacing)
        else:
            # Normal
            draw.multiline_text(
                position,
                text,
                fill=fill,
                font=self.font,
                align=align,
                spacing=spacing
            )

    def _draw_italic_text(self, draw, position, text, fill, align="center", spacing=4):
        """Simulate italic text by shearing"""
        from PIL import Image
        
        # Get text size
        bbox = draw.textbbox((0, 0), text, font=self.font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Create temp image for text
        temp_img = Image.new('RGBA', (text_width + 20, text_height + 20), (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp_img)
        temp_draw.text((10, 10), text, fill=fill, font=self.font, align=align, spacing=spacing)
        
        # Apply shear transformation (0.2 = ~11 degrees slant)
        temp_img = temp_img.transform(
            temp_img.size,
            Image.Transform.AFFINE,
            (1, 0.2, 0, 0, 1, 0),
            Image.Resampling.BILINEAR
        )
        
        # Paste onto main canvas
        draw._image.paste(temp_img, (int(position[0] - 10), int(position[1] - 10)), temp_img)

    def _draw_bold_italic_text(self, draw, position, text, fill, align="center", spacing=4):
        """Simulate bold italic text"""
        from PIL import Image
        
        # Get text size
        bbox = draw.textbbox((0, 0), text, font=self.font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Create temp image
        temp_img = Image.new('RGBA', (text_width + 30, text_height + 30), (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp_img)
        
        # Draw multiple times for bold
        offsets = [(0,0), (1,0), (0,1), (1,1)]
        x, y = 15, 15
        for dx, dy in offsets:
            temp_draw.text((x + dx, y + dy), text, fill=fill, font=self.font, align=align, spacing=spacing)
        
        # Apply shear for italic
        temp_img = temp_img.transform(
            temp_img.size,
            Image.Transform.AFFINE,
            (1, 0.2, 0, 0, 1, 0),
            Image.Resampling.BILINEAR
        )
        
        # Paste
        draw._image.paste(temp_img, (int(position[0] - 15), int(position[1] - 15)), temp_img)

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
        total_text_height = len(line_list) * (line_height * 1.2)
        return int(total_text_height + self.TOP_PADDING + self.BOTTOM_PADDING)
    
    def _get_text_position(self, text):
        """Calculate top-left corner position for centered text."""
        line_list = text.split('\n')
        max_w = max(self._get_text_dimensions(line)[0] for line in line_list)
        return ((self.width - max_w) / 2, self.TOP_PADDING)
    
    def _get_text_position_bottom(self, text, y_offset):
        """Calculate top-left corner position for centered bottom text."""
        line_list = text.split('\n')
        max_w = max(self._get_text_dimensions(line)[0] for line in line_list)
        return ((self.width - max_w) / 2, y_offset + self.TOP_PADDING)
    
    def _get_text_position_bottom_overlay(self, text):
        """Calculate position for bottom text overlay on the image."""
        line_list = text.split('\n')
        max_w = max(self._get_text_dimensions(line)[0] for line in line_list)
        
        _, line_height = self._get_text_dimensions(line_list[0])
        total_text_height = len(line_list) * (line_height * 1.2)
        
        y_position = self.height - total_text_height - self.BOTTOM_PADDING
        
        if y_position < self.TOP_PADDING:
            y_position = self.TOP_PADDING
            
        return ((self.width - max_w) / 2, y_position)
    
    def generate(self):
        """
        Generate the captioned image.
        
        Returns:
            PIL.Image: The captioned image
        """
        wrapped_top_text = self._process_text()
        top_text_height = self._calculate_text_height(wrapped_top_text)
        
        bottom_text_height = 0
        wrapped_bottom_text = None
        if self.bottom_text:
            wrapped_bottom_text = "\n".join([
                self._wrap_text(line, self.width) 
                for line in self.bottom_text.split("\n")
            ])
            bottom_text_height = self._calculate_text_height(wrapped_bottom_text)
            
            if self.bottom_text_box:
                max_allowed_height = int(self.height * self.MAX_BOTTOM_TEXT_HEIGHT_RATIO)
                if bottom_text_height > max_allowed_height:
                    pass
        
        if self.bottom_text_box or not self.bottom_text:
            total_height = top_text_height + self.height + bottom_text_height
            canvas = Image.new("RGB", (self.width, total_height), (255, 255, 255))
            canvas.paste(self.image, (0, top_text_height))
        else:
            total_height = top_text_height + self.height
            canvas = Image.new("RGB", (self.width, total_height), (255, 255, 255))
            canvas.paste(self.image, (0, top_text_height))
        
        draw = ImageDraw.Draw(canvas)
        
        if self.top_background_color:
            draw.rectangle(
                [(0, 0), (self.width, top_text_height)],
                fill=self.top_background_color
            )
        
        if self.separator_line:
            line_y = top_text_height - 1
            draw.line([(0, line_y), (self.width, line_y)], fill=self.separator_line_color, width=2)
        
        top_text_pos = self._get_text_position(wrapped_top_text)
        
#        draw.multiline_text(
#            top_text_pos,
#            wrapped_top_text,
#            fill=self.top_font_color,
#            font=self.font,
#            align="center",
#            spacing=4
#        )

        self._draw_text_with_style(
            draw,
            top_text_pos,
            wrapped_top_text,
            fill=self.top_font_color,
            align="center",
            spacing=4
        )
        
        if self.bottom_text and wrapped_bottom_text:
            if self.bottom_text_box:
                # Draw bottom background if specified
                if self.bottom_background_color:
                    bottom_bg_y = top_text_height + self.height
                    draw.rectangle(
                        [(0, bottom_bg_y), (self.width, bottom_bg_y + bottom_text_height)],
                        fill=self.bottom_background_color
                    )
                
                bottom_text_pos = self._get_text_position_bottom(wrapped_bottom_text, top_text_height + self.height)
                
#                draw.multiline_text(
#                    bottom_text_pos,
#                    wrapped_bottom_text,
#                    fill=self.bottom_font_color,
#                    font=self.font,
#                    align="center",
#                    spacing=4
#                )

                self._draw_text_with_style(
                    draw,
                    bottom_text_pos,
                    wrapped_bottom_text,
                    fill=self.top_font_color,
                    align="center",
                    spacing=4
                )
                
                if self.separator_line:
                    line_y = top_text_height + self.height
                    draw.line([(0, line_y), (self.width, line_y)], fill=self.separator_line_color, width=2)
            else:
                overlay_text_pos = self._get_text_position_bottom_overlay(wrapped_bottom_text)
                adjusted_y = overlay_text_pos[1] + top_text_height
                
#                draw.multiline_text(
#                    (overlay_text_pos[0], adjusted_y),
#                    wrapped_bottom_text,
#                    fill=self.bottom_font_color,
#                    font=self.font,
#                    align="center",
#                    spacing=4
#                )

                self._draw_text_with_style(
                    draw,
                    (overlay_text_pos[0], adjusted_y),
                    wrapped_bottom_text,
                    fill=self.bottom_font_color,
                    align="center",
                    spacing=4
                )
        
        return canvas

    def to_buffer(self, format="JPEG", max_size=None):
        """Generate captioned image and return (buffer, extension)."""
        if self._is_animated_gif():
            buffer = self.generate_gif()
            ext = "gif"
            if max_size:
                buffer = self.compress_to_size(buffer, max_size, original_format='GIF')
            return buffer, ext
        else:
            captioned_image = self.generate()
            buffer = io.BytesIO()
            
            # Determine actual format based on image and input
            if format.upper() == 'PNG':
                # Save as PNG first
                captioned_image.save(buffer, format='PNG')
                ext = 'png'
            else:
                # Default to JPEG
                if captioned_image.mode in ('RGBA', 'LA', 'P'):
                    # Convert to RGB for JPEG
                    rgb_image = Image.new('RGB', captioned_image.size, (255, 255, 255))
                    if captioned_image.mode == 'RGBA':
                        rgb_image.paste(captioned_image, mask=captioned_image.split()[3])
                    else:
                        rgb_image.paste(captioned_image)
                    rgb_image.save(buffer, format='JPEG', quality=95)
                else:
                    captioned_image.save(buffer, format='JPEG', quality=95)
                ext = 'jpg'
            
            buffer.seek(0)
            
            # Compress if needed
            if max_size:
                # Pass the actual format for compression
                original_format = 'PNG' if ext == 'png' else 'JPEG'
                buffer = self.compress_to_size(buffer, max_size, original_format)
            
            return buffer, ext


    def close(self):
        """Close the underlying PIL Image to free memory."""
        if hasattr(self, 'image'):
            self.image.close()
    
    def save(self, output_path, max_size=None):
        """Generate and save the captioned image."""
        if self._is_animated_gif():
            gif_buffer = self.generate_gif()
            
            # Compress if needed
            if max_size:
                gif_buffer = self.compress_to_size(gif_buffer, max_size, original_format='GIF')
            
            # Write directly to file
            with open(output_path, 'wb') as f:
                f.write(gif_buffer.getvalue())
        else:
            captioned_image = self.generate()
            
            # Compress if needed
            if max_size:
                buffer = io.BytesIO()
                
                # Determine format from file extension
                if output_path.lower().endswith('.png'):
                    # Save as PNG first
                    captioned_image.save(buffer, format='PNG')
                    original_format = 'PNG'
                else:
                    # Save as JPEG (default)
                    if captioned_image.mode in ('RGBA', 'LA', 'P'):
                        # Convert to RGB for JPEG with white background
                        rgb_image = Image.new('RGB', captioned_image.size, (255, 255, 255))
                        if captioned_image.mode == 'RGBA':
                            rgb_image.paste(captioned_image, mask=captioned_image.split()[3])
                        else:
                            rgb_image.paste(captioned_image)
                        rgb_image.save(buffer, format='JPEG', quality=95)
                    else:
                        captioned_image.save(buffer, format='JPEG', quality=95)
                    original_format = 'JPEG'
                
                buffer.seek(0)
                
                # Compress
                compressed = self.compress_to_size(buffer, max_size, original_format)
                
                # Write compressed buffer directly to file
                with open(output_path, 'wb') as f:
                    f.write(compressed.getvalue())
            else:
                # No compression, save directly
                if output_path.lower().endswith('.png'):
                    captioned_image.save(output_path, format='PNG')
                else:
                    if captioned_image.mode in ('RGBA', 'LA', 'P'):
                        # Convert to RGB for JPEG with white background
                        rgb_image = Image.new('RGB', captioned_image.size, (255, 255, 255))
                        if captioned_image.mode == 'RGBA':
                            rgb_image.paste(captioned_image, mask=captioned_image.split()[3])
                        else:
                            rgb_image.paste(captioned_image)
                        rgb_image.save(output_path, format='JPEG', quality=95)
                    else:
                        captioned_image.save(output_path, format='JPEG', quality=95)
        
        return output_path