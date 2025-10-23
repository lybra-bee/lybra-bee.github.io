import re
import sys

def escape_markdown(text):
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(r'([%s])' % re.escape(escape_chars), r'\\\1', text)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python escape_markdown.py '<title>' '<url>'")
        sys.exit(1)

    title = sys.argv[1]
    url = sys.argv[2]

    title_escaped = escape_markdown(title)
    url_escaped = escape_markdown(url)

    message = f"📢 *Новый пост*: \"{title_escaped}\"\n🔗 [Читать пост]({url_escaped})"

    print(message)
