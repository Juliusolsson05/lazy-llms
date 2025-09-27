import markdown
import bleach
from datetime import datetime
from markupsafe import Markup

# Allowed HTML tags for markdown rendering
ALLOWED_TAGS = [
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'p', 'br', 'strong', 'em', 'u', 'del', 'ins',
    'ul', 'ol', 'li', 'blockquote', 'code', 'pre',
    'a', 'img', 'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'hr', 'div', 'span'
]

ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
    'code': ['class'],
    'pre': ['class'],
    'div': ['class'],
    'span': ['class']
}

def render_markdown(text):
    """Convert markdown text to safe HTML."""
    if not text:
        return ""

    # Convert markdown to HTML
    html = markdown.markdown(
        text,
        extensions=[
            'markdown.extensions.fenced_code',
            'markdown.extensions.tables',
            'markdown.extensions.toc',
            'markdown.extensions.nl2br'
        ]
    )

    # Sanitize HTML to prevent XSS
    clean_html = bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )

    return Markup(clean_html)

def truncate_text(text, length=150):
    """Truncate text to specified length with ellipsis."""
    if not text:
        return ""

    # Remove markdown formatting for display
    plain_text = bleach.clean(text, tags=[], strip=True)

    if len(plain_text) <= length:
        return plain_text

    return plain_text[:length].rsplit(' ', 1)[0] + '...'

def extract_summary(description):
    """Extract a summary from the description markdown."""
    if not description:
        return "No description available."

    lines = description.split('\n')

    # Find first meaningful paragraph (skip headers and empty lines)
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('```'):
            return truncate_text(line, 200)

    return "No description available."

def format_date(date_obj, format='%Y-%m-%d'):
    """Format date object or string safely"""
    if not date_obj:
        return 'N/A'

    if isinstance(date_obj, str):
        # Handle ISO string format
        try:
            if date_obj.endswith('Z'):
                date_obj = date_obj[:-1]  # Remove Z
            dt = datetime.fromisoformat(date_obj)
            return dt.strftime(format)
        except ValueError:
            return date_obj[:10] if len(date_obj) >= 10 else date_obj

    if isinstance(date_obj, datetime):
        return date_obj.strftime(format)

    return str(date_obj)

def format_datetime(date_obj, format='%Y-%m-%d %H:%M'):
    """Format datetime object or string safely"""
    return format_date(date_obj, format)