
from PIL import Image, ImageDraw
import os

ICON_CACHE_DIR = "icon_cache"
if not os.path.exists(ICON_CACHE_DIR):
    os.makedirs(ICON_CACHE_DIR)

def create_icon(name, draw_func, size=(24, 24)):
    filepath = os.path.join(ICON_CACHE_DIR, f"{name}.png")
    if os.path.exists(filepath):
        return filepath

    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw_func(draw, size)
    image.save(filepath)
    return filepath

def draw_connect_icon(draw, size):
    # A simple representation of a plug and socket
    draw.rectangle((2, 8, 10, 16), outline="green", width=2)
    draw.line((10, 10, 18, 10), fill="green", width=2)
    draw.line((10, 14, 18, 14), fill="green", width=2)
    draw.rectangle((18, 8, 22, 16), outline="green", width=2)

def draw_disconnect_icon(draw, size):
    # A broken plug/socket
    draw.rectangle((2, 8, 10, 16), outline="red", width=2)
    draw.line((10, 10, 15, 10), fill="red", width=2)
    draw.line((10, 14, 15, 14), fill="red", width=2)
    draw.rectangle((18, 8, 22, 16), outline="red", width=2)
    draw.line((5, 5, 19, 19), fill="red", width=2) # A cross

def draw_wake_icon(draw, size):
    # A simple sun/power symbol
    center = (size[0] // 2, size[1] // 2)
    draw.ellipse((center[0]-5, center[1]-5, center[0]+5, center[1]+5), outline="#FFD700", width=2)
    for i in range(8):
        angle = i * 45
        x1 = center[0] + 7
        y1 = center[1]
        x2 = center[0] + 10
        y2 = center[1]
        # Basic rotation logic needed here, simplified for now
        draw.line((x1,y1,x2,y2), fill="#FFD700", width=2)

def draw_rdp_icon(draw, size):
    # A simple monitor screen
    draw.rectangle((4, 4, 20, 20), outline="#4682B4", width=2)
    draw.rectangle((6, 6, 18, 18), fill="#4682B4")
    draw.line((8, 20, 16, 20), fill="#4682B4", width=2)
    draw.line((12, 20, 12, 22), fill="#4682B4", width=2)

def draw_pc_icon(draw, size):
    # A simple desktop PC tower with a screen
    # PC Tower
    draw.rectangle((size[0]*0.2, size[1]*0.3, size[0]*0.5, size[1]*0.8), outline="#95a5a6", width=2)
    draw.rectangle((size[0]*0.25, size[1]*0.35, size[0]*0.45, size[1]*0.45), fill="#95a5a6") # CD-ROM
    draw.ellipse((size[0]*0.3, size[1]*0.6, size[0]*0.4, size[1]*0.7), fill="#95a5a6") # Power button

    # Monitor
    draw.rectangle((size[0]*0.55, size[1]*0.2, size[0]*0.85, size[1]*0.6), outline="#4682B4", width=2)
    draw.line((size[0]*0.7, size[1]*0.6, size[0]*0.7, size[1]*0.7), fill="#4682B4", width=2) # Stand

def get_all_icons():
    return {
        "connect": create_icon("connect", draw_connect_icon),
        "disconnect": create_icon("disconnect", draw_disconnect_icon),
        "wake": create_icon("wake", draw_wake_icon),
        "rdp": create_icon("rdp", draw_rdp_icon),
        "pc": create_icon("pc", draw_pc_icon) # Add the PC icon
    }

def get_app_icon():
    return create_icon("app_icon", draw_rdp_icon, size=(32,32))
