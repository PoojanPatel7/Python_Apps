"""Generate Task Manager icon."""
from PIL import Image, ImageDraw
import os

SIZE = 256
C = SIZE // 2

def create_icon():
    img = Image.new("RGBA", (SIZE, SIZE), (10, 10, 15, 255))
    d = ImageDraw.Draw(img)

    # Background
    d.rounded_rectangle([C-90, C-90, C+90, C+90], radius=24,
                        fill=(18, 18, 30, 255), outline=(40, 50, 80, 255), width=2)

    # 3 bars
    colors = [(0, 180, 255), (120, 80, 255), (255, 80, 180)]
    heights = [90, 65, 110]
    bw, gap = 28, 12
    sx = C - (3 * bw + 2 * gap) // 2
    by = C + 55

    for i in range(3):
        x1 = sx + i * (bw + gap)
        y1 = by - heights[i]
        d.rounded_rectangle([x1, y1, x1 + bw, by], radius=6, fill=(*colors[i], 230))

    # X button
    cx, cy = C + 52, C - 52
    d.ellipse([cx-16, cy-16, cx+16, cy+16], fill=(255, 50, 70, 220))
    d.line([(cx-7, cy-7), (cx+7, cy+7)], fill=(255, 255, 255), width=3)
    d.line([(cx+7, cy-7), (cx-7, cy+7)], fill=(255, 255, 255), width=3)

    sd = os.path.dirname(os.path.abspath(__file__))
    img.save(os.path.join(sd, "icon.png"), "PNG")
    sizes = [(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)]
    icons = [img.resize(s, Image.LANCZOS) for s in sizes]
    icons[0].save(os.path.join(sd, "icon.ico"), format="ICO", sizes=sizes, append_images=icons[1:])
    print("Icon created!")

if __name__ == "__main__":
    create_icon()
