#!/usr/bin/env python3
"""One-shot: replace plaintext email addresses / mailto links in the served
HTML with JS-assembled equivalents (see email-protect.js). Idempotent and
reviewable via `git diff`. Run from the repo root."""

import base64
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADDR = "djz@shmonk.com"
ADDR_B64 = base64.b64encode(ADDR.encode()).decode()
FALLBACK_TEXT = "djz [at] shmonk [dot] com"
SCRIPT_TAG = '  <script src="/email-protect.js" defer></script>\n'

FILES = [
    "index.html", "about.html", "contact.html", "coaching.html",
    "teaching.html", "writing.html", "organizations.html",
    "coaching-onepager.html", "organizations-onepager.html",
    "corporate-coaching-brief.html",
]


def b64(s):
    return base64.b64encode(s.encode()).decode()


def transform(html):
    changed = False

    # 1. mailto links -> href="/contact" fallback + data-e base64 target.
    def repl_link(m):
        target = m.group(1)
        return 'href="/contact" data-e="%s"' % b64(target)
    html, n = re.subn(r'href="mailto:([^"]*)"', repl_link, html)
    changed = changed or n > 0

    # 2. Anchor whose visible text is the bare address: show it via JS, and
    #    leave a bot-safe placeholder for the no-JS case.
    html = html.replace(
        'data-e="%s">%s</a>' % (ADDR_B64, ADDR),
        'data-e="%s" data-e-show>%s</a>' % (ADDR_B64, FALLBACK_TEXT),
    )
    # 3. Remaining bare plaintext addresses (e.g. one-pager footers).
    if ADDR in html:
        html = html.replace(
            ADDR,
            '<span data-e-text="%s">%s</span>' % (ADDR_B64, FALLBACK_TEXT),
        )
        changed = True

    # 4. Ensure the protector script is loaded (once, before </body>).
    if changed and "email-protect.js" not in html:
        html = html.replace("</body>", SCRIPT_TAG + "</body>", 1)

    return html, changed


def main():
    total = 0
    for name in FILES:
        p = ROOT / name
        if not p.exists():
            print("skip (missing):", name)
            continue
        original = p.read_text()
        if "data-e" in original or "data-e-text" in original:
            print("skip (already done):", name)
            continue
        new, changed = transform(original)
        if changed:
            p.write_text(new)
            total += 1
            print("updated:", name)
        else:
            print("no change:", name)
    print("\n%d file(s) updated." % total)


if __name__ == "__main__":
    main()
