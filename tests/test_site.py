"""Structural spec for the Sam Smith Joinery static site.

These tests are the contract for the site: every page must be present, self-contained
(no external CDN calls), accessible in the basics, and carry the business contact
details. Written before the HTML exists, so they define the build rather than describe it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path

import pytest

SITE_ROOT = Path(__file__).resolve().parent.parent

PAGES = [
    "index.html",
    "about.html",
    "services.html",
    "gallery.html",
    "booking.html",
    "contact.html",
]

BUSINESS_NAME = "Sam Smith Joinery"
# Ofcom-reserved fictional number so the placeholder can never dial a real person.
PHONE_DISPLAY = "07700 900123"
PHONE_TEL = "+447700900123"
EMAIL = "sam@samsmithjoinery.co.uk"

VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}

# Fields the booking form must collect, keyed by the `name` attribute.
REQUIRED_BOOKING_FIELDS = [
    "name",
    "email",
    "phone",
    "service",
    "preferred-date",
    "details",
]


@dataclass
class Tag:
    name: str
    attrs: dict[str, str]


class SiteParser(HTMLParser):
    """Collects the handful of facts the tests assert on."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: list[Tag] = []
        self.open_stack: list[str] = []
        self.unbalanced: list[str] = []
        self.text_by_tag: dict[str, list[str]] = {}
        self._current: list[str] = []
        self.has_doctype = False

    def handle_decl(self, decl: str) -> None:
        if decl.lower().startswith("doctype html"):
            self.has_doctype = True

    def handle_starttag(self, tag: str, attrs) -> None:
        self.tags.append(Tag(tag, {k: (v or "") for k, v in attrs}))
        if tag not in VOID_TAGS:
            self.open_stack.append(tag)
        self._current.append(tag)

    def handle_startendtag(self, tag: str, attrs) -> None:
        self.tags.append(Tag(tag, {k: (v or "") for k, v in attrs}))

    def handle_endtag(self, tag: str) -> None:
        if tag in VOID_TAGS:
            return
        if not self.open_stack or self.open_stack[-1] != tag:
            self.unbalanced.append(f"</{tag}> closed while {self.open_stack[-3:]} open")
            if tag in self.open_stack:
                while self.open_stack and self.open_stack.pop() != tag:
                    pass
            return
        self.open_stack.pop()

    def handle_data(self, data: str) -> None:
        if self._current and data.strip():
            self.text_by_tag.setdefault(self._current[-1], []).append(data.strip())

    def find(self, name: str) -> list[Tag]:
        return [t for t in self.tags if t.name == name]


def parse(page: str) -> SiteParser:
    parser = SiteParser()
    parser.feed((SITE_ROOT / page).read_text(encoding="utf-8"))
    return parser


def raw(page: str) -> str:
    return (SITE_ROOT / page).read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def parsed() -> dict[str, SiteParser]:
    return {page: parse(page) for page in PAGES}


# --- presence -------------------------------------------------------------


@pytest.mark.parametrize("page", PAGES)
def test_page_exists_and_is_not_empty(page: str) -> None:
    path = SITE_ROOT / page
    assert path.is_file(), f"missing page: {page}"
    assert len(path.read_text(encoding="utf-8")) > 500, f"{page} looks like a stub"


def test_stylesheet_and_script_exist() -> None:
    assert (SITE_ROOT / "assets/css/styles.css").is_file()
    assert (SITE_ROOT / "assets/js/main.js").is_file()


# --- document head --------------------------------------------------------


@pytest.mark.parametrize("page", PAGES)
def test_doctype_lang_charset_and_viewport(page: str, parsed) -> None:
    doc = parsed[page]
    assert doc.has_doctype, f"{page}: missing <!doctype html>"

    html_tags = doc.find("html")
    assert html_tags and html_tags[0].attrs.get("lang") == "en-GB", f"{page}: needs lang=en-GB"

    metas = doc.find("meta")
    assert any("charset" in m.attrs for m in metas), f"{page}: missing charset"
    assert any(
        m.attrs.get("name") == "viewport" and "width=device-width" in m.attrs.get("content", "")
        for m in metas
    ), f"{page}: missing responsive viewport"


@pytest.mark.parametrize("page", PAGES)
def test_has_title_and_meta_description(page: str, parsed) -> None:
    doc = parsed[page]
    titles = doc.text_by_tag.get("title", [])
    assert titles, f"{page}: missing <title>"
    assert BUSINESS_NAME in titles[0], f"{page}: title must carry the business name"

    descriptions = [
        m.attrs.get("content", "")
        for m in doc.find("meta")
        if m.attrs.get("name") == "description"
    ]
    assert descriptions, f"{page}: missing meta description"
    assert 50 <= len(descriptions[0]) <= 165, f"{page}: meta description length off ({len(descriptions[0])})"


def test_titles_are_unique(parsed) -> None:
    titles = [parsed[page].text_by_tag["title"][0] for page in PAGES]
    assert len(set(titles)) == len(titles), f"duplicate <title> values: {titles}"


# --- structure and accessibility -----------------------------------------


@pytest.mark.parametrize("page", PAGES)
def test_exactly_one_h1(page: str, parsed) -> None:
    h1s = parsed[page].find("h1")
    assert len(h1s) == 1, f"{page}: expected 1 <h1>, found {len(h1s)}"


@pytest.mark.parametrize("page", PAGES)
def test_tags_are_balanced(page: str, parsed) -> None:
    doc = parsed[page]
    assert not doc.unbalanced, f"{page}: unbalanced markup -> {doc.unbalanced[:3]}"
    assert not doc.open_stack, f"{page}: tags left open -> {doc.open_stack}"


@pytest.mark.parametrize("page", PAGES)
def test_landmarks_present(page: str, parsed) -> None:
    doc = parsed[page]
    for landmark in ("header", "nav", "main", "footer"):
        assert doc.find(landmark), f"{page}: missing <{landmark}> landmark"


@pytest.mark.parametrize("page", PAGES)
def test_skip_link_is_first_focusable(page: str, parsed) -> None:
    anchors = parsed[page].find("a")
    assert anchors, f"{page}: no links at all"
    assert anchors[0].attrs.get("href") == "#main", f"{page}: first link should be a skip link to #main"


@pytest.mark.parametrize("page", PAGES)
def test_every_image_has_alt_text(page: str, parsed) -> None:
    for img in parsed[page].find("img"):
        assert "alt" in img.attrs, f"{page}: <img src={img.attrs.get('src')}> has no alt attribute"


@pytest.mark.parametrize("page", PAGES)
def test_decorative_svgs_are_hidden_from_screen_readers(page: str, parsed) -> None:
    for svg in parsed[page].find("svg"):
        labelled = svg.attrs.get("role") == "img" and "aria-label" in svg.attrs
        hidden = svg.attrs.get("aria-hidden") == "true"
        assert labelled or hidden, f"{page}: <svg> needs aria-hidden=true or role=img + aria-label"


# --- navigation and links -------------------------------------------------


@pytest.mark.parametrize("page", PAGES)
def test_nav_links_to_every_page(page: str) -> None:
    nav_html = re.search(r"<nav\b.*?</nav>", raw(page), re.S)
    assert nav_html, f"{page}: no <nav> block"
    for target in PAGES:
        assert f'href="{target}"' in nav_html.group(0), f"{page}: nav is missing a link to {target}"


@pytest.mark.parametrize("page", PAGES)
def test_current_page_is_marked_in_nav(page: str, parsed) -> None:
    current = [
        a for a in parsed[page].find("a")
        if a.attrs.get("aria-current") == "page"
    ]
    assert len(current) == 1, f"{page}: exactly one nav link must carry aria-current=page"
    assert current[0].attrs.get("href") == page


@pytest.mark.parametrize("page", PAGES)
def test_internal_links_resolve(page: str, parsed) -> None:
    for tag_name, attr in (("a", "href"), ("link", "href"), ("script", "src"), ("img", "src")):
        for tag in parsed[page].find(tag_name):
            target = tag.attrs.get(attr, "")
            if not target or target.startswith(("http://", "https://", "mailto:", "tel:", "#", "data:")):
                continue
            resolved = (SITE_ROOT / target.split("#")[0].split("?")[0]).resolve()
            assert resolved.exists(), f"{page}: <{tag_name} {attr}={target}> does not resolve"


@pytest.mark.parametrize("page", PAGES)
def test_no_external_assets(page: str, parsed) -> None:
    """The site must work offline from a USB stick - no CDN, no tracker, no web font call."""
    for tag_name, attr in (("link", "href"), ("script", "src"), ("img", "src")):
        for tag in parsed[page].find(tag_name):
            target = tag.attrs.get(attr, "")
            assert not target.startswith(("http://", "https://", "//")), (
                f"{page}: external asset {target} - inline or vendor it instead"
            )


# --- contact details ------------------------------------------------------


@pytest.mark.parametrize("page", PAGES)
def test_footer_carries_contact_details(page: str) -> None:
    footer = re.search(r"<footer\b.*?</footer>", raw(page), re.S)
    assert footer, f"{page}: no <footer>"
    block = footer.group(0)
    assert PHONE_DISPLAY in block, f"{page}: footer missing phone number"
    assert EMAIL in block, f"{page}: footer missing email address"
    assert BUSINESS_NAME in block, f"{page}: footer missing business name"


@pytest.mark.parametrize("page", PAGES)
def test_phone_and_email_are_click_to_action(page: str, parsed) -> None:
    hrefs = [a.attrs.get("href", "") for a in parsed[page].find("a")]
    assert f"tel:{PHONE_TEL}" in hrefs, f"{page}: phone must be a tel: link using {PHONE_TEL}"
    assert f"mailto:{EMAIL}" in hrefs, f"{page}: email must be a mailto: link"


def test_no_real_looking_contact_details_leak_in() -> None:
    """Placeholder site - guard against a plausible-but-real number or address sneaking in."""
    for page in PAGES:
        text = raw(page)
        for match in re.findall(r"\b0(?:7\d{3}|1\d{3}|20)\s?\d{3}\s?\d{3,4}\b", text):
            digits = re.sub(r"\s", "", match)
            assert digits.startswith("07700900") or digits.startswith("01134960"), (
                f"{page}: {match} is not in an Ofcom drama-reserved range"
            )


# --- content depth --------------------------------------------------------


def test_services_page_lists_enough_services() -> None:
    articles = re.findall(r'<article class="service-card"', raw("services.html"))
    assert len(articles) >= 8, f"expected 8+ service cards, found {len(articles)}"


def test_gallery_has_captioned_items() -> None:
    html = raw("gallery.html")
    figures = re.findall(r"<figure\b.*?</figure>", html, re.S)
    assert len(figures) >= 6, f"expected 6+ gallery items, found {len(figures)}"
    for figure in figures:
        assert "<figcaption" in figure, "every gallery item needs a <figcaption>"


def test_homepage_has_testimonials() -> None:
    assert re.search(r"<blockquote\b", raw("index.html")), "homepage should carry testimonials"


def test_homepage_has_call_to_action_to_booking() -> None:
    assert 'href="booking.html"' in raw("index.html"), "homepage needs a booking CTA"


def test_icons_are_inline_svg() -> None:
    """Icons must be embedded, not fetched - see the licence note in README."""
    assert len(re.findall(r"<svg\b", raw("index.html"))) >= 4
    assert (SITE_ROOT / "README.md").is_file(), "README must record icon licensing"
    readme = (SITE_ROOT / "README.md").read_text(encoding="utf-8")
    assert "licen" in readme.lower(), "README must state the icon licence"


# --- booking form ---------------------------------------------------------


@pytest.fixture(scope="module")
def booking() -> SiteParser:
    return parse("booking.html")


def test_booking_page_has_one_form(booking) -> None:
    forms = booking.find("form")
    assert len(forms) == 1, f"expected exactly 1 form on booking.html, found {len(forms)}"
    assert forms[0].attrs.get("method", "").lower() == "post"
    assert forms[0].attrs.get("action"), "form needs an action for the real endpoint to drop into"
    assert forms[0].attrs.get("novalidate") is not None, "JS handles validation messaging"


@pytest.mark.parametrize("field", REQUIRED_BOOKING_FIELDS)
def test_booking_form_collects_field(field: str, booking) -> None:
    controls = booking.find("input") + booking.find("select") + booking.find("textarea")
    names = [c.attrs.get("name") for c in controls]
    assert field in names, f"booking form missing a control named {field!r} (has {names})"


def test_booking_form_controls_are_labelled(booking) -> None:
    label_targets = {lbl.attrs.get("for") for lbl in booking.find("label")}
    controls = booking.find("input") + booking.find("select") + booking.find("textarea")
    for control in controls:
        if control.attrs.get("type") in {"hidden", "submit"}:
            continue
        control_id = control.attrs.get("id")
        assert control_id, f"control {control.attrs.get('name')} has no id to label"
        assert control_id in label_targets, f"no <label for={control_id}> on the booking form"


def test_booking_form_marks_required_fields(booking) -> None:
    controls = booking.find("input") + booking.find("select") + booking.find("textarea")
    required = {c.attrs.get("name") for c in controls if "required" in c.attrs}
    for field in ("name", "email", "service", "details"):
        assert field in required, f"{field} should be a required field"


def test_booking_form_has_honeypot_and_consent(booking) -> None:
    names = [c.attrs.get("name") for c in booking.find("input")]
    assert "company-website" in names, "expected a honeypot field to blunt spam bots"
    assert "consent" in names, "expected a GDPR consent checkbox"


def test_booking_date_field_is_a_date_input(booking) -> None:
    date_inputs = [
        i for i in booking.find("input")
        if i.attrs.get("name") == "preferred-date"
    ]
    assert date_inputs and date_inputs[0].attrs.get("type") == "date"


def test_service_select_options_match_services_page() -> None:
    select = re.search(r'<select id="service".*?</select>', raw("booking.html"), re.S)
    assert select, "booking.html has no service dropdown"
    options = re.findall(r"<option[^>]*>([^<]+)</option>", select.group(0))
    real_options = [o.strip() for o in options if "choose" not in o.lower()]
    assert len(real_options) >= 8, f"service dropdown should offer every service, found {real_options}"
    services_html = raw("services.html")
    for option in real_options:
        if option.lower().startswith("something else"):
            continue
        assert option in services_html, f"booking offers {option!r} but services.html never mentions it"


# --- behaviour / assets ---------------------------------------------------


def test_javascript_is_clean() -> None:
    js = (SITE_ROOT / "assets/js/main.js").read_text(encoding="utf-8")
    assert "console.log" not in js, "strip debug logging"
    assert "addEventListener" in js
    assert "'use strict'" in js or '"use strict"' in js


def test_javascript_validates_the_booking_form() -> None:
    js = (SITE_ROOT / "assets/js/main.js").read_text(encoding="utf-8")
    assert "booking-form" in js, "JS must wire up the booking form by id"
    assert "checkValidity" in js or "validity" in js


def test_css_is_responsive_and_themed() -> None:
    css = (SITE_ROOT / "assets/css/styles.css").read_text(encoding="utf-8")
    assert "@media" in css, "no responsive breakpoints"
    assert "--" in css, "expected CSS custom properties for the palette"
    assert "prefers-reduced-motion" in css, "respect reduced-motion"
    assert ":focus-visible" in css, "keyboard focus styling is required"
