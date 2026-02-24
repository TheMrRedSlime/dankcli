import os
import sys
import argparse
import datetime
from .caption import Caption


def get_file_name():
    """Generate timestamp-based filename."""
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S")


def parse_color(color_str):
    """Parse color string in format R,G,B or R G B."""
    if not color_str:
        return None
    
    # Try comma-separated first
    if ',' in color_str:
        try:
            r, g, b = map(int, color_str.split(','))
            return (r, g, b)
        except ValueError:
            pass
    
    # Try space-separated
    try:
        r, g, b = map(int, color_str.split())
        return (r, g, b)
    except ValueError:
        raise ValueError(f"Invalid color format. Use R,G,B or R G B (e.g., '255,255,255')")


def main():
    parser = argparse.ArgumentParser(prog="dankcli_lib", description="Add captions to images with various styling options")
    
    # Required arguments
    parser.add_argument("img", help="Path to the source image")
    parser.add_argument("text", help="Text to caption (use \\n for new lines)")
    
    # Output options
    parser.add_argument("-f", "--filename", help="Custom output filename (without extension)")
    
    # Font options
    parser.add_argument("--font", default="arial.ttf", help="Path to font file (default: arial.ttf)")
    
    # Top text options
    parser.add_argument("--top_font_color", help="Top text color as R,G,B or R G B (e.g., '0,0,0' for black)")
    parser.add_argument("--top_bg_color", help="Top background color as R,G,B or R G B (e.g., '255,255,255' for white)")
    
    # Bottom text options
    parser.add_argument("--bottom_text", help="Text to place at the bottom of the image")
    parser.add_argument("--bottom_text_box", action="store_true", default=True,
                        help="Add white box for bottom text (default: True)")
    parser.add_argument("--no-bottom-text-box", dest="bottom_text_box", action="store_false",
                        help="Overlay bottom text directly on image without box")
    parser.add_argument("--bottom_font_color", help="Bottom text color as R,G,B or R G B (e.g., '255,255,255' for white)")
    parser.add_argument("--bottom_bg_color", help="Bottom background color as R,G,B or R G B (e.g., '255,255,255' for white)")
    
    # Separator line options
    parser.add_argument("--separator_line", action="store_true", 
                        help="Draw a line separating the caption from the image")
    parser.add_argument("--separator_color", default="0,0,0",
                        help="Separator line color as R,G,B or R G B (default: '0,0,0' for black)")
    
    args = parser.parse_args()

    # Resolve image path
    img_path = os.path.abspath(os.path.expanduser(args.img))
    
    # Check if image exists
    if not os.path.exists(img_path):
        print(f"Error: Image file not found: {img_path}")
        sys.exit(1)
    
    try:
        # Parse color arguments
        top_font_color = parse_color(args.top_font_color) if args.top_font_color else None
        top_bg_color = parse_color(args.top_bg_color) if args.top_bg_color else None
        bottom_font_color = parse_color(args.bottom_font_color) if args.bottom_font_color else None
        bottom_bg_color = parse_color(args.bottom_bg_color) if args.bottom_bg_color else None
        separator_color = parse_color(args.separator_color)
        
        # Create Caption instance with all options
        caption = Caption(
            img_path, 
            args.text, 
            font_path=args.font, 
            separator_line=args.separator_line,
            separator_line_color=separator_color,
            bottom_text=args.bottom_text,
            bottom_text_box=args.bottom_text_box,
            top_font_color=top_font_color,
            bottom_font_color=bottom_font_color,
            top_background_color=top_bg_color,
            bottom_background_color=bottom_bg_color
        )
        
        # Determine output filename and extension
        out_name = args.filename if args.filename else get_file_name()
        # Check if image has transparency or if we're using overlay text (no box)
        # PNG supports transparency better, but we'll let the user specify format eventually
        is_jpeg = img_path.lower().endswith(('.jpg', '.jpeg'))
        extension = "jpg" if is_jpeg else "png"
        extension = "gif" if img_path.lower().endswith(".gif") else "png"
        output_path = f"{out_name}.{extension}"
        
        # Generate and save
        caption.save(output_path)
        print(f"Meme saved successfully: {output_path}")
        
    except Exception as e:
        print(f"Error: Could not process image. {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()