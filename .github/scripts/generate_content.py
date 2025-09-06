#!/usr/bin/env python3
# coding: utf-8
"""
generate_content.py
OpenRouter/GROQ -> text
FusionBrain -> image
Creates:
 - content/_index.md (new homepage)
 - content/posts/<slug>/index.md (page bundle) + image.png inside
 - static/images/gallery/<slug>.png (copy)
Keeps 5 articles total (home + 4 posts).
"""
import os, sys, time, json, re, textwrap, base64, shutil, logging, requests
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger("gen")

CONTENT_DIR = "content"
POSTS_DIR = os.path.join(CONTENT_DIR, "posts")
GALLERY_DIR = os.path.join("static", "images", "gallery")
KEEP = 5

def slugify(text):
    t = (text or "ai-article").lower()
    t = re.sub(r'[^a-z0-9\s\-]', '', t.replace('ё','e'))
    t = re.sub(r'[\s_]+', '-', t)
    t = re.sub(r'-+', '-', t).strip('-')
    stamp = str(int(time.time()))[-5:]
    return (t[:40] + "-" + stamp) if t else ("ai-article-" + stamp)

def ensure_dirs():
    os.makedirs(POSTS_DIR, exist_ok=True)
    os.makedirs(GALLERY_DIR, exist_ok=True)
    os.makedirs(os.path.join(CONTENT_DIR), exist_ok=True)

def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# Text generation
def prompt_text():
    return ("Напиши развернутую профессиональную статью на русском языке о современных "
            "тенденциях в области нейросетей и высоких технологий (фокус — 2024–2025 годы). "
            "Объём 500–800 слов. Формат — Markdown с заголовками (##, ###). "
            "Аудитория — разработчики и технические менеджеры. "
            "Включи: краткое введение, 3-4 технических раздела с примерами/кейcами, вывод/перспективы. "
            "Добавь краткое summary в начале (2-3 предложения).")

def gen_openrouter(api_key, prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type":"application/json"}
    payload = {"model":"anthropic/claude-3-haiku","messages":[{"role":"user","content":prompt}], "max_tokens":1500, "temperature":0.7}
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    if r.status_code==200:
        data = r.json()
        if data.get("choices"):
            choice = data["choices"][0].get("message") or data["choices"][0].get("text")
            if isinstance(choice, dict):
                return choice.get("content") or choice.get("content", {}).get("parts", [None])[0]
            return choice
    raise RuntimeError(f"OpenRouter failed {r.status_code}: {r.text}")

def gen_groq(api_key, prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type":"application/json"}
    payload = {"model":"llama-3.1-8b-instant","messages":[{"role":"user","content":prompt}], "max_tokens":1500, "temperature":0.7}
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    if r.status_code==200:
        data = r.json()
        if data.get("choices"):
            return data["choices"][0]["message"]["content"]
    raise RuntimeError(f"GROQ failed {r.status_code}: {r.text}")

# FusionBrain image
class FusionBrain:
    def __init__(self, key, secret):
        self.base = "https://api-key.fusionbrain.ai/"
        self.headers = {"X-Key": f"Key {key}", "X-Secret": f"Secret {secret}"}
    def list_pipelines(self):
        r = requests.get(self.base + "key/api/v1/pipelines", headers=self.headers, timeout=15)
        return r.json() if r.status_code==200 else None
    def run(self, pipeline_id, prompt):
        params = {"type":"GENERATE","numImages":1,"width":1024,"height":512,"generateParams":{"query":prompt}}
        files = {"params": (None, json.dumps(params), "application/json"), "pipeline_id": (None, pipeline_id)}
        r = requests.post(self.base + "key/api/v1/pipeline/run", headers=self.headers, files=files, timeout=30)
        if r.status_code in (200,201): return r.json()
        raise RuntimeError(f"Fusion run failed {r.status_code}: {r.text}")
    def status(self, uuid):
        r = requests.get(self.base + f"key/api/v1/pipeline/status/{uuid}", headers=self.headers, timeout=15)
        return r.json() if r.status_code==200 else None

def generate_image_fusion(key, secret, prompt, attempts=25, delay=4):
    fb = FusionBrain(key, secret)
    pipelines = fb.list_pipelines()
    if not pipelines: raise RuntimeError("No Fusion pipelines")
    pid = next((p["id"] for p in pipelines if "kandinsky" in p.get("name","").lower()), pipelines[0]["id"])
    run = fb.run(pid, prompt)
    uuid = run.get("uuid") or run.get("id")
    if not uuid: raise RuntimeError("No task id")
    for i in range(attempts):
        if i>0: time.sleep(delay)
        st = fb.status(uuid)
        if not st: continue
        if st.get("status")=="DONE":
            res = st.get("result", {})
            files = res.get("files") or []
            if files:
                first = files[0]
                if isinstance(first, dict) and first.get("url"):
                    rr = requests.get(first.get("url"), timeout=30)
                    if rr.status_code==200: return rr.content
                # try base64 field
                b64 = first.get("base64") or first.get("data")
                if b64:
                    return base64.b64decode(b64)
            # sometimes result as data:image...
            if isinstance(res, str) and res.startswith("data:image"):
                idx = res.find("base64,")
                if idx!=-1: return base64.b64decode(res[idx+7:])
        elif st.get("status") in ("FAIL","ERROR"):
            raise RuntimeError(f"Fusion failed: {st}")
    raise RuntimeError("Fusion timeout")

# file helpers
def write_bytes(path, b):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path,"wb") as f: f.write(b)

def write_text(path, s):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path,"w",encoding="utf-8") as f: f.write(s)

# page bundle & gallery creation
def create_bundle_and_gallery(slug, title, content_md, image_bytes):
    post_dir = os.path.join(POSTS_DIR, slug)
    os.makedirs(post_dir, exist_ok=True)
    # image inside bundle
    bundle_img = os.path.join(post_dir, "image.png")
    write_bytes(bundle_img, image_bytes)
    # gallery copy
    gallery_img = os.path.join(GALLERY_DIR, f"{slug}.png")
    write_bytes(gallery_img, image_bytes)
    # index.md
    fm = [
        "---",
        f'title: "{title.replace("\"","\'")}"',
        f"date: {now_iso()}",
        'draft: false',
        'tags: ["ai","технологии","2025"]',
        'categories: ["Искусственный интеллект"]',
        'image: "image.png"',
        '---',
        "",
    ]
    md = "\n".join(fm) + content_md
    write_text(os.path.join(post_dir,"index.md"), md)
    return bundle_img, gallery_img

def now_iso(): return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def move_home_to_posts():
    home = os.path.join(CONTENT_DIR,"_index.md")
    if not os.path.exists(home): return
    txt = open(home,"r",encoding="utf-8").read()
    title = None
    m = re.search(r'^title:\s*"(.*?)"', txt, flags=re.MULTILINE)
    if m: title = m.group(1)
    else:
        m2 = re.search(r'^\#\s*(.+)', txt, flags=re.MULTILINE)
        if m2: title = m2.group(1).strip()
    slug = slugify(title or "moved")
    dest = os.path.join(POSTS_DIR, slug); os.makedirs(dest,exist_ok=True)
    shutil.move(home, os.path.join(dest,"index.md"))
    log.info(f"Moved previous home to posts/{slug}")

def create_home(title, md_content, gallery_rel_path):
    home_path = os.path.join(CONTENT_DIR, "_index.md")
    fm = [
        "---",
        f'title: "{title.replace("\"","\'")}"',
        f"date: {now_iso()}",
        "draft: false",
        f'image: "{gallery_rel_path}"',
        'tags: ["ai","технологии","2025"]',
        '---',
        "",
    ]
    write_text(home_path, "\n".join(fm) + md_content)

def prune_keep(keep=KEEP):
    # keep home + (keep-1) newest post bundles
    bundles = []
    if os.path.exists(POSTS_DIR):
        for name in os.listdir(POSTS_DIR):
            idx = os.path.join(POSTS_DIR,name,"index.md")
            if os.path.exists(idx):
                bundles.append((os.path.getmtime(idx), os.path.join(POSTS_DIR,name)))
    bundles.sort(reverse=True)
    allowed = max(0, keep-1)
    for _, b in bundles[allowed:]:
        try:
            shutil.rmtree(b)
            log.info(f"Removed old bundle {b}")
        except Exception as e:
            log.warning(f"Remove failed {b}: {e}")

def main():
    ensure_dirs()
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    fusion_key = os.getenv("FUSIONBRAIN_API_KEY")
    fusion_secret = os.getenv("FUSION_SECRET_KEY")

    prompt = prompt_text()
    md = None

    # OpenRouter first
    if openrouter_key:
        try:
            log.info("Generating text via OpenRouter...")
            md = gen_openrouter(openrouter_key, prompt)
            log.info("OpenRouter success")
        except Exception as e:
            log.warning(f"OpenRouter fail: {e}")

    if not md and groq_key:
        try:
            log.info("Generating text via GROQ...")
            md = gen_groq(groq_key, prompt)
            log.info("GROQ success")
        except Exception as e:
            log.warning(f"GROQ fail: {e}")

    if not md:
        log.warning("Text generation failed — using fallback content")
        md = "# Тенденции AI\n\nFallback content."

    # Extract title
    title = None
    for line in md.splitlines():
        if line.strip().startswith("# "):
            title = line.strip()[2:].strip(); break
    if not title:
        title = "Тенденции AI " + datetime.now().strftime("%Y-%m-%d")

    slug = slugify(title)
    log.info(f"Title: {title} / slug: {slug}")

    # Generate image
    img_bytes = None
    if fusion_key and fusion_secret:
        try:
            log.info("Generating image via FusionBrain...")
            img_bytes = generate_image_fusion(fusion_key, fusion_secret, f"{title} — futuristic digital art, AI, high quality")
            log.info("Image generated")
        except Exception as e:
            log.warning(f"Fusion failed: {e}")

    if not img_bytes:
        # create simple png placeholder
        try:
            from PIL import Image, ImageDraw, ImageFont
            w,h = 1200,600
            img = Image.new("RGB",(w,h),(15,23,42))
            d = ImageDraw.Draw(img)
            text = textwrap.fill(title, width=40)
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",32)
            except:
                font = None
            d.text((40,h//2-60), text, fill=(255,255,255), font=font)
            import io
            buf = io.BytesIO(); img.save(buf, format="PNG"); img_bytes = buf.getvalue()
            log.info("Created placeholder image")
        except Exception as e:
            log.error("Placeholder creation failed: " + str(e))
            img_bytes = b''

    # move existing home into posts
    try: move_home_to_posts()
    except Exception as e: log.warning(f"move_home_to_posts failed: {e}")

    # create post bundle and gallery
    try:
        bundle_img, gallery_img = create_bundle_and_gallery(slug, title, md, img_bytes)
    except Exception as e:
        log.error(f"Failed to create bundle/gallery: {e}")
        sys.exit(1)

    # create homepage pointing to static gallery image (relative path under static)
    gallery_rel = f"images/gallery/{slug}.png"
    create_home(title, md, gallery_rel)

    # prune older posts
    prune_keep(KEEP)

    log.info("Generation finished.")

if __name__ == '__main__':
    main()
