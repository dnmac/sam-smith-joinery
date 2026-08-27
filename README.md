# Sam Smith Joinery — example website

A six-page static marketing site for a sole-trader joiner. Plain HTML, one stylesheet,
one small JavaScript file. **No build step, no framework, no npm install.** Open
`index.html` in a browser and it works — including straight off a USB stick.

All names, numbers, prices, reviews and photographs are placeholders. Swap them for the
real ones before this goes anywhere near a customer (see *Swapping in real details*).

## Pages

| File | Purpose |
|---|---|
| `index.html` | Home — hero, services preview, why-choose-us, process, work preview, reviews |
| `about.html` | Who Sam is, qualifications, insurance |
| `services.html` | All ten services in detail, plus guide prices |
| `gallery.html` | Portfolio with client-side category filtering |
| `booking.html` | Free-quote booking form |
| `contact.html` | Phone, email, hours, coverage area, map placeholder |

## Running it

```bash
cd sam-smith-joinery
python3 -m http.server 8000    # then open http://localhost:8000
```

Opening the files directly with `file://` works too.

## Tests

```bash
python3 -m pytest tests/ -q
```

The tests are a structural contract, not decoration: every page exists, markup is
balanced, every image has alt text, every form control has a label, all internal links
resolve, no asset is fetched from an external host, the booking dropdown never offers a
service the services page does not mention, and the placeholder phone numbers stay inside
Ofcom's drama-reserved ranges so the site can never dial a real person.

## Icons

Every icon is **inline SVG hand-drawn on a 24×24 grid specifically for this site**. There
is no icon library, no font, no CDN request and therefore **no third-party licence to
comply with and no attribution required** — they are yours to use, change or delete.

If you would rather swap in an off-the-shelf set later, these are the safe free options:

| Set | Licence | Attribution needed? |
|---|---|---|
| [Lucide](https://lucide.dev) | ISC | Keep the copyright notice in the source |
| [Tabler Icons](https://tabler.io/icons) | MIT | Keep the copyright notice in the source |
| [Phosphor](https://phosphoricons.com) | MIT | Keep the copyright notice in the source |
| [Font Awesome Free](https://fontawesome.com) | CC BY 4.0 (icons) | **Yes** — visible credit |

Download and inline the SVG rather than linking a CDN, so the site stays self-contained.

## Photographs

`assets/img/*.svg` are generated placeholders. Replace each one with a real photo,
**keeping the same filename** (change the extension in the `<img src>` if you use `.jpg`).
Aim for 4:3, around 1200×900, compressed to under 300 KB.

## Making the booking form actually send

Right now the form validates, then shows a confirmation in the page without sending
anything — that is the `data-demo="true"` attribute on `<form id="booking-form">`.

To go live, pick a form back end (Formspree, Netlify Forms, Basin, Web3Forms — all have
free tiers), then in `booking.html`:

1. Replace `action="https://formspree.io/f/REPLACE-WITH-YOUR-FORM-ID"` with your real endpoint.
2. Delete the `data-demo="true"` attribute.

Client-side validation, the honeypot spam trap and the GDPR consent checkbox keep working.

## Swapping in real details

Search and replace across all six HTML files:

| Placeholder | Replace with |
|---|---|
| `Sam Smith Joinery` | Real trading name |
| `07700 900123` / `+447700900123` | Real mobile (both display text and the `tel:` link) |
| `0113 496 0123` / `+441134960123` | Real landline, or delete the line |
| `sam@samsmithjoinery.co.uk` | Real email (display text and the `mailto:` link) |
| Guide prices in `services.html` | Real numbers |
| Testimonials in `index.html` | Real reviews, with permission |
| Areas listed in the footer | Real coverage |

Then run the tests again — several of them will fail until the phone-number guard in
`tests/test_site.py` is updated to the real numbers, which is the reminder that the
change landed everywhere.

## Colours

Set once as CSS custom properties at the top of `assets/css/styles.css` — change
`--timber`, `--amber` and `--sand` and the whole site follows.
