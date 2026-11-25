import os
import random

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(ROOT, "documents", "_extract", "fixtures")

FONTS = [r"C:\Windows\Fonts\msgothic.ttc", r"C:\Windows\Fonts\meiryo.ttc", r"C:\Windows\Fonts\arial.ttf"]


def font(size, bold=False):
    for path in FONTS:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size, index=1 if bold else 0)
            except Exception:
                continue
    return ImageFont.load_default()


def payment_screenshot(path):
    w, h = 780, 1500
    img = Image.new("RGB", (w, h), "#0b1020")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w, 120], fill="#141b2d")
    d.text((36, 52), "9:41", font=font(26), fill="#e8edf7")
    d.text((w - 120, 52), "5G  ▮", font=font(22), fill="#8fa0bd")
    y = 180
    d.ellipse([w // 2 - 46, y, w // 2 + 46, y + 92], fill="#16a34a")
    d.line([(w // 2 - 18, y + 46), (w // 2 - 4, y + 62), (w // 2 + 22, y + 30)], fill="white", width=8)
    y += 130
    d.text((w // 2 - 96, y), "振込が完了しました", font=font(34), fill="#e8edf7")
    y += 90
    d.text((w // 2 - 130, y), "¥3,200", font=font(64), fill="#ffffff")
    y += 110
    rows = [
        ("日時", "2026年11月25日 14:32"),
        ("振込先", "東京電力エナジーパートナー"),
        ("口座", "普通 ****3821"),
        ("手数料", "0円"),
        ("合計", "3,200円"),
    ]
    for label, value in rows:
        d.text((48, y), label, font=font(24), fill="#8fa0bd")
        d.text((230, y), value, font=font(26), fill="#e8edf7")
        y += 74
        d.line([(48, y - 18), (w - 48, y - 18)], fill="#1c2537", width=1)
    y += 40
    d.rectangle([40, y, w - 40, y + 96], fill="#1d4ed8")
    d.text((w // 2 - 66, y + 32), "閉じる", font=font(30), fill="#ffffff")
    img.save(path, "PNG")
    return path


def not_payment(path):
    w, h = 780, 1100
    img = Image.new("RGB", (w, h), "#2a2f3a")
    d = ImageDraw.Draw(img)
    for _ in range(9000):
        x = random.randint(0, w - 1)
        y = random.randint(0, h - 1)
        g = random.randint(30, 120)
        d.point((x, y), fill=(g, g, g + 8))
    d.text((60, 80), "メモ", font=font(30), fill="#c8d0dd")
    d.text((60, 150), "牛乳を買う", font=font(28), fill="#98a2b3")
    d.text((60, 210), "歯ブラシ", font=font(28), fill="#98a2b3")
    img.save(path, "PNG")
    return path


def main():
    os.makedirs(OUT, exist_ok=True)
    a = payment_screenshot(os.path.join(OUT, "payment_screenshot.png"))
    b = not_payment(os.path.join(OUT, "not_payment.png"))
    for path in (a, b):
        print(path, os.path.getsize(path), "bytes")


if __name__ == "__main__":
    main()
