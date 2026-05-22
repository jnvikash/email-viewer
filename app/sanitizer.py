import re
import bleach
from bleach.css_sanitizer import CSSSanitizer

ALLOWED_TAGS = [
    "a", "abbr", "b", "blockquote", "br", "caption", "code",
    "col", "colgroup", "dd", "del", "div", "dl", "dt", "em",
    "h1", "h2", "h3", "h4", "h5", "h6", "hr", "i", "img",
    "ins", "kbd", "li", "ol", "p", "pre", "q", "s", "small",
    "span", "strong", "sub", "sup", "table", "tbody", "td",
    "tfoot", "th", "thead", "tr", "u", "ul", "font", "center",
]

ALLOWED_ATTRS = {
    "*": ["class", "id", "style", "align", "valign", "dir", "lang"],
    "a": ["href", "title", "target", "rel"],
    "img": ["src", "alt", "width", "height", "border"],
    "td": ["colspan", "rowspan", "width", "height", "bgcolor", "nowrap"],
    "th": ["colspan", "rowspan", "width", "height"],
    "table": ["width", "border", "cellpadding", "cellspacing", "bgcolor"],
    "font": ["size", "color", "face"],
    "col": ["width", "span"],
    "colgroup": ["width", "span"],
}

ALLOWED_CSS = [
    "color", "background-color", "background", "font-size", "font-weight",
    "font-style", "font-family", "text-align", "text-decoration",
    "padding", "padding-top", "padding-bottom", "padding-left", "padding-right",
    "margin", "margin-top", "margin-bottom", "margin-left", "margin-right",
    "border", "border-top", "border-bottom", "border-left", "border-right",
    "border-collapse", "width", "height", "max-width", "min-width",
    "line-height", "vertical-align", "display", "float", "clear",
    "white-space", "word-wrap", "overflow",
]

_css_sanitizer = CSSSanitizer(allowed_css_properties=ALLOWED_CSS)

# Strip <base> tags before bleach sees them
_BASE_RE = re.compile(r"<base[^>]*>", re.IGNORECASE)
# Detect data: URI size abuse (>5MB base64)
_DATA_URI_LARGE_RE = re.compile(r'src\s*=\s*["\']data:[^"\']{5242880,}["\']', re.IGNORECASE)
# Extract <style> blocks (including any attributes on the tag)
_STYLE_BLOCK_RE = re.compile(r"<style[^>]*>(.*?)</style>", re.IGNORECASE | re.DOTALL)
# Extract body content
_BODY_RE = re.compile(r"<body[^>]*>(.*?)</body>", re.IGNORECASE | re.DOTALL)
# Dangerous CSS patterns to strip from <style> blocks
_CSS_DANGEROUS_RE = re.compile(
    r"expression\s*\(|javascript\s*:|behavior\s*:|-moz-binding\s*:|@import\b",
    re.IGNORECASE,
)


def _clean_attrs(tag, name, value):
    """Attribute cleaner: block javascript: hrefs, strip large data URIs."""
    if name == "href":
        stripped = value.strip().lower().replace("\x00", "")
        if stripped.startswith("javascript:") or stripped.startswith("vbscript:"):
            return None
    if name == "src":
        stripped = value.strip().lower()
        if stripped.startswith("data:") and len(value) > 5_242_880:
            return None  # block huge data URIs
    return value


def _extract_style_blocks(html: str) -> tuple[str, str]:
    """Extract <style> blocks from HTML, returning (sanitized_css, html_without_styles)."""
    css_parts = []

    def collect_style(m):
        css = m.group(1)
        # Remove dangerous CSS patterns
        css = _CSS_DANGEROUS_RE.sub("/* removed */", css)
        css_parts.append(css)
        return ""

    html_without_styles = _STYLE_BLOCK_RE.sub(collect_style, html)
    return "\n".join(css_parts), html_without_styles


def _extract_body_content(html: str) -> str:
    """Return the content between <body> and </body>, falling back to full html."""
    m = _BODY_RE.search(html)
    return m.group(1) if m else html


def sanitize_html(html: str, email_id: int = 0, attachments: list = None) -> str:
    """Clean HTML email body for safe iframe rendering."""
    if not html:
        return ""

    # Strip <base> tags
    html = _BASE_RE.sub("", html)

    # Rewrite CID references to attachment preview URLs
    if attachments:
        cid_map = {}
        for att in attachments:
            name = att.get("filename", "")
            idx = att.get("attach_index", 0)
            cid_map[name.lower()] = f"/api/attachments/{email_id}/{idx}/preview"

        def rewrite_cid(m):
            full, cid_val = m.group(0), m.group(1).lower()
            for name, url in cid_map.items():
                if name in cid_val or cid_val.replace("cid:", "") in name:
                    return full.replace(m.group(1), url)
            return full

        html = re.sub(r'src=["\']cid:([^"\']+)["\']', rewrite_cid, html, flags=re.IGNORECASE)

    # Extract and sanitize <style> blocks before bleach strips them as text
    sanitized_css, html = _extract_style_blocks(html)

    # Feed only the body content to bleach (avoids <head> junk appearing as text)
    body_content = _extract_body_content(html)

    cleaned = bleach.clean(
        body_content,
        tags=ALLOWED_TAGS,
        attributes=_clean_attrs,
        css_sanitizer=_css_sanitizer,
        strip=True,
        strip_comments=True,
    )

    # Force all links to open in new tab safely
    cleaned = re.sub(
        r'(<a\s)',
        r'\1target="_blank" rel="noopener noreferrer" ',
        cleaned,
        flags=re.IGNORECASE,
    )

    # Prepend sanitized styles so email CSS applies correctly
    if sanitized_css:
        cleaned = f"<style>{sanitized_css}</style>{cleaned}"

    return cleaned


def text_to_html(text: str) -> str:
    """Convert plain text to basic HTML for display."""
    import html as html_module
    escaped = html_module.escape(text)
    return f"<pre style='white-space:pre-wrap;font-family:inherit'>{escaped}</pre>"
