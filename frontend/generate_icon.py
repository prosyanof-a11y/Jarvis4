"""Generate ICO icon from SVG for desktop shortcut."""
import os
import struct

def create_ico_from_bmp_data():
    """Create a simple 32x32 ICO file with Iron Man mask colors."""
    size = 32
    
    # Iron Man mask pixel art (32x32)
    # Colors: 0=transparent, 1=dark red, 2=gold, 3=cyan glow, 4=dark bg
    palette = {
        0: (0, 0, 0, 0),        # transparent
        1: (192, 57, 43, 255),   # red helmet
        2: (245, 197, 24, 255),  # gold face
        3: (0, 212, 255, 255),   # cyan eyes
        4: (26, 26, 46, 255),    # dark bg
        5: (139, 0, 0, 255),     # dark red
        6: (184, 134, 11, 255),  # dark gold
    }
    
    # 32x32 pixel art of Iron Man mask (top to bottom)
    mask = [
        "00000000000000000000000000000000",
        "00000000000111111111000000000000",
        "00000000011111111111110000000000",
        "00000001111111111111111100000000",
        "00000011111111111111111110000000",
        "00000111111111111111111111000000",
        "00001111111111111111111111100000",
        "00011111111122222222111111110000",
        "00011111112222222222211111110000",
        "00111111122222222222221111111000",
        "00111111222222222222222111111000",
        "01111112222222222222222211111100",
        "01111122222222222222222221111100",
        "01111122234422222244322221111100",
        "01111122233442222244332221111100",
        "01111122233344224443332221111100",
        "01111122233334444433332221111100",
        "01111122233333333333332221111100",
        "01111122222222222222222221111100",
        "01111112222222222222222211111100",
        "00111111222226666662222111111000",
        "00111111222226666662222111111000",
        "00111111122226666622221111111000",
        "00011111112222666622211111110000",
        "00011111111222222222111111110000",
        "00001111111122222221111111100000",
        "00000111111112222211111111000000",
        "00000011111111222111111110000000",
        "00000001111111111111111100000000",
        "00000000011111111111110000000000",
        "00000000000111111111000000000000",
        "00000000000000000000000000000000",
    ]
    
    # Create RGBA pixel data (bottom-up for BMP)
    pixels = bytearray()
    for row in reversed(mask):
        for ch in row:
            r, g, b, a = palette.get(int(ch), (0, 0, 0, 0))
            pixels.extend([b, g, r, a])  # BGRA format
    
    # AND mask (transparency mask, 1 bit per pixel, padded to 4 bytes per row)
    and_mask = bytearray()
    for row in reversed(mask):
        row_bits = 0
        for i, ch in enumerate(row):
            if ch == '0':
                row_bits |= (1 << (31 - i))
        and_mask.extend(struct.pack('>I', row_bits))
    
    # BMP info header (BITMAPINFOHEADER)
    bmp_header = struct.pack('<IiiHHIIiiII',
        40,          # header size
        size,        # width
        size * 2,    # height (doubled for ICO: XOR + AND)
        1,           # planes
        32,          # bits per pixel
        0,           # compression (none)
        len(pixels) + len(and_mask),  # image size
        0, 0,        # pixels per meter
        0, 0         # colors
    )
    
    image_data = bmp_header + bytes(pixels) + bytes(and_mask)
    
    # ICO file header
    ico_header = struct.pack('<HHH', 0, 1, 1)  # reserved, type=ICO, count=1
    
    # ICO directory entry
    ico_entry = struct.pack('<BBBBHHII',
        size,        # width
        size,        # height
        0,           # color count
        0,           # reserved
        1,           # planes
        32,          # bits per pixel
        len(image_data),  # size of image data
        6 + 16       # offset to image data (header=6 + entry=16)
    )
    
    ico_data = ico_header + ico_entry + image_data
    
    # Save
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "jarvis.ico")
    os.makedirs(os.path.dirname(icon_path), exist_ok=True)
    with open(icon_path, 'wb') as f:
        f.write(ico_data)
    
    print(f"Icon saved to: {icon_path}")
    return icon_path


if __name__ == "__main__":
    create_ico_from_bmp_data()
