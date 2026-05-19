"""Generate a Speed Checker app icon programmatically."""

from PIL import Image, ImageDraw, ImageFont
import math
import os

SIZE = 256
CENTER = SIZE // 2
RADIUS = 100

def create_icon():
    img = Image.new("RGBA", (SIZE, SIZE), (10, 10, 15, 255))
    draw = ImageDraw.Draw(img)

    # ── Outer glow ring ──────────────────────────────────────
    for r in range(RADIUS + 20, RADIUS + 8, -1):
        alpha = int(30 * (1 - (r - RADIUS - 8) / 12))
        draw.ellipse(
            [CENTER - r, CENTER - r, CENTER + r, CENTER + r],
            outline=(0, 229, 255, alpha), width=1
        )

    # ── Background circle ────────────────────────────────────
    draw.ellipse(
        [CENTER - RADIUS, CENTER - RADIUS, CENTER + RADIUS, CENTER + RADIUS],
        fill=(18, 18, 26, 255), outline=(30, 30, 48, 255), width=2
    )

    # ── Speed arc — cyan (download) ──────────────────────────
    arc_r = RADIUS - 12
    start_angle = 150
    end_angle = 300
    for i in range(start_angle, end_angle):
        t = (i - start_angle) / (end_angle - start_angle)
        rad = math.radians(i)
        x = CENTER + arc_r * math.cos(rad)
        y = CENTER + arc_r * math.sin(rad)

        # Cyan gradient
        r_c = int(0 + t * 0)
        g_c = int(180 + t * 75)
        b_c = int(200 + t * 55)
        
        for w in range(4):
            wx = CENTER + (arc_r - w) * math.cos(rad)
            wy = CENTER + (arc_r - w) * math.sin(rad)
            draw.point((int(wx), int(wy)), fill=(r_c, g_c, b_c, 255))

    # ── Speed arc — magenta (upload) ─────────────────────────
    for i in range(end_angle, 390):
        t = (i - end_angle) / (390 - end_angle)
        rad = math.radians(i)
        
        r_c = int(212 + t * 43)
        g_c = int(0)
        b_c = int(180 + t * 49)
        
        for w in range(4):
            wx = CENTER + (arc_r - w) * math.cos(rad)
            wy = CENTER + (arc_r - w) * math.sin(rad)
            draw.point((int(wx), int(wy)), fill=(r_c, g_c, b_c, 255))

    # ── Tick marks ───────────────────────────────────────────
    for i in range(0, 11):
        angle = 150 + i * (240 / 10)
        rad = math.radians(angle)
        inner_r = RADIUS - 24
        outer_r = RADIUS - 16
        
        x1 = CENTER + inner_r * math.cos(rad)
        y1 = CENTER + inner_r * math.sin(rad)
        x2 = CENTER + outer_r * math.cos(rad)
        y2 = CENTER + outer_r * math.sin(rad)
        
        color = (100, 100, 140, 255) if i % 5 != 0 else (200, 200, 220, 255)
        width = 1 if i % 5 != 0 else 2
        draw.line([(x1, y1), (x2, y2)], fill=color, width=width)

    # ── Needle (pointing to ~75% position) ───────────────────
    needle_angle = 150 + 0.75 * 240  # 75% speed
    needle_rad = math.radians(needle_angle)
    needle_len = RADIUS - 30
    
    nx = CENTER + needle_len * math.cos(needle_rad)
    ny = CENTER + needle_len * math.sin(needle_rad)
    
    # Needle shadow
    draw.line(
        [(CENTER + 1, CENTER + 1), (nx + 1, ny + 1)],
        fill=(0, 0, 0, 100), width=4
    )
    # Needle body
    draw.line(
        [(CENTER, CENTER), (nx, ny)],
        fill=(0, 229, 255, 255), width=3
    )
    # Needle tip glow
    draw.ellipse(
        [nx - 5, ny - 5, nx + 5, ny + 5],
        fill=(0, 229, 255, 200)
    )
    # Center dot
    draw.ellipse(
        [CENTER - 8, CENTER - 8, CENTER + 8, CENTER + 8],
        fill=(30, 30, 50, 255), outline=(0, 229, 255, 255), width=2
    )

    # ── Down arrow (bottom left) ─────────────────────────────
    ax, ay = CENTER - 30, CENTER + 40
    draw.polygon(
        [(ax, ay + 12), (ax - 7, ay), (ax + 7, ay)],
        fill=(0, 229, 255, 200)
    )
    draw.line([(ax, ay - 8), (ax, ay)], fill=(0, 229, 255, 200), width=3)

    # ── Up arrow (bottom right) ──────────────────────────────
    ax2, ay2 = CENTER + 30, CENTER + 40
    draw.polygon(
        [(ax2, ay2 - 8), (ax2 - 7, ay2 + 4), (ax2 + 7, ay2 + 4)],
        fill=(255, 0, 229, 200)
    )
    draw.line([(ax2, ay2 + 4), (ax2, ay2 + 14)], fill=(255, 0, 229, 200), width=3)

    # ── Save as PNG and ICO ──────────────────────────────────
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    png_path = os.path.join(script_dir, "icon.png")
    img.save(png_path, "PNG")
    print(f"Saved: {png_path}")

    ico_path = os.path.join(script_dir, "icon.ico")
    # Create multiple sizes for the ICO
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    icons = [img.resize(s, Image.LANCZOS) for s in sizes]
    icons[0].save(ico_path, format="ICO", sizes=sizes, append_images=icons[1:])
    print(f"Saved: {ico_path}")


if __name__ == "__main__":
    create_icon()
