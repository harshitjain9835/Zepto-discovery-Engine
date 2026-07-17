from pathlib import Path

root = Path(r"g:\nextleap\Grad Project\Zepto Review Analyse")
templates = [
    "Delivery was fast and the order arrived on time.",
    "I trust the routine for staples, but I hesitate for premium items.",
    "The checkout felt slow and the app froze during payment.",
    "Packaging quality felt risky and I worried about damage.",
    "Support resolved my issue quickly and that improved confidence.",
    "Fresh produce looked good, though stock was inconsistent.",
    "The basket suggestions made weekly shopping much easier.",
    "I liked the search and discovery flow for new products.",
    "The order arrived late and that hurt my plans.",
    "I avoid personal care products because the quality feels inconsistent.",
    "The app is great for repeat orders of milk and bread.",
    "Customer service responded fast when I needed help.",
    "I would recommend the service for essentials, but not for skincare.",
    "The app makes repeat groceries easy and convenient.",
    "I found the delivery promise reliable most of the time.",
    "The packaging looked damaged and untrustworthy.",
    "I was happy with the price, but the support experience felt weak.",
    "The recommendations helped me discover snacks and household items.",
    "I am confident buying staples, but not trying unfamiliar brands.",
    "The refund process was delayed and that reduced trust.",
]

entries = []
for i in range(1, 201):
    base = templates[(i - 1) % len(templates)]
    entries.append(f"{base} #{i:03d}")

output_path = root / "reviews.txt"
output_path.write_text("\n".join(entries) + "\n", encoding="utf-8")
print(f"wrote {len(entries)} reviews to {output_path}")
