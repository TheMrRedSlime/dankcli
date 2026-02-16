import os
import sys
import argparse
import datetime
from .caption import Caption


def get_file_name():
    """Generate timestamp-based filename."""
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S")


def main():
    parser = argparse.ArgumentParser(prog="dankcli")
    parser.add_argument("img", help="Path to the source image")
    parser.add_argument("text", help="Text to caption (use \\n for new lines)")
    parser.add_argument("-f", "--filename", help="Custom output filename")
    parser.add_argument("--font", default="arial.ttf", help="Path to font file")
    parser.add_argument("--separator_line", action="store_true", 
                        help="Draw a black line separating the caption from the image")
    parser.add_argument("--bottom_text", help="Text to place at the bottom of the image")
    parser.add_argument("--top_font_color", help="Top text color as R,G,B (e.g., '0,0,0' for black)")
    parser.add_argument("--bottom_font_color", help="Bottom text color as R,G,B (e.g., '255,255,255' for white)")
    args = parser.parse_args()

    # Resolve image path
    img_path = os.path.abspath(os.path.expanduser(args.img))
    
    # Check if image exists
    if not os.path.exists(img_path):
        print(f"Error: Image file not found: {img_path}")
        sys.exit(1)
    
    try:
        # Parse color arguments
        top_font_color = None
        bottom_font_color = None
        
        if args.top_font_color:
            try:
                r, g, b = map(int, args.top_font_color.split(','))
                top_font_color = (r, g, b)
            except ValueError:
                print(f"Error: Invalid top_font_color format. Use R,G,B (e.g., '0,0,0')")
                sys.exit(1)
        
        if args.bottom_font_color:
            try:
                r, g, b = map(int, args.bottom_font_color.split(','))
                bottom_font_color = (r, g, b)
            except ValueError:
                print(f"Error: Invalid bottom_font_color format. Use R,G,B (e.g., '255,255,255')")
                sys.exit(1)
        
        # Create Caption instance
        caption = Caption(
            img_path, 
            args.text, 
            font_path=args.font, 
            separator_line=args.separator_line,
            bottom_text=args.bottom_text,
            top_font_color=top_font_color,
            bottom_font_color=bottom_font_color
        )
        
        # Determine output filename and extension
        out_name = args.filename if args.filename else get_file_name()
        is_jpeg = img_path.lower().endswith(('.jpg', '.jpeg'))
        extension = "jpg" if is_jpeg else "png"
        output_path = f"{out_name}.{extension}"
        
        # Generate and save
        caption.save(output_path)
        print(f"Meme saved successfully: {output_path}")
        
    except Exception as e:
        print(f"Error: Could not process image. {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()