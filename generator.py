import json
import os
import textwrap
import pyttsx3
import requests
from PIL import Image, ImageDraw, ImageFont

try:
    from moviepy import AudioFileClip, ImageClip, concatenate_videoclips
    _MOVIEPY_V2 = True
except ImportError:
    from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips
    _MOVIEPY_V2 = False

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()


def _load_font(size: int, bold: bool = False):
    candidates = (
        ["arialbd.ttf", "DejaVuSans-Bold.ttf", "arial.ttf"]
        if bold
        else ["arial.ttf", "DejaVuSans.ttf"]
    )
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def make_text_content(topic: str) -> dict:
    clean_tag = "".join(ch for ch in topic.title() if ch.isalnum()) or "CreatorTips"
    fallback = {
        "script": (
            f"Here is a quick reel on {topic}. "
            f"First, understand why {topic} matters today. "
            f"Second, apply one practical step consistently. "
            f"Save this and share with a friend."
        ),
        "caption": f"Everything you need to know about {topic} in under 30 seconds.",
        "hashtags": f"#{clean_tag} #AIReels #TechTips #Learning #Shorts",
    }

    if not GEMINI_API_KEY:
        return fallback

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    prompt = (
        f"Create a short engaging 25-second reel script on '{topic}'. "
        "Return ONLY valid JSON with exact keys: script, caption, hashtags. "
        "Keep script to 3-4 clear spoken sentences with no markdown or emojis."
    )
    try:
        r = requests.post(
            url,
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseMimeType": "application/json"},
            },
            timeout=20,
        )
        r.raise_for_status()
        raw = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        data = json.loads(raw)
        if all(k in data for k in ("script", "caption", "hashtags")):
            return {
                "script": str(data["script"]).strip(),
                "caption": str(data["caption"]).strip(),
                "hashtags": str(data["hashtags"]).strip(),
            }
    except Exception:
        pass

    return fallback


def _split_slides(script: str, max_slides: int = 3) -> list[str]:
    parts = [p.strip() for p in script.replace("\n", " ").split(".") if p.strip()]
    if not parts:
        return ["AI Reels Generator"]
    if len(parts) <= max_slides:
        return [p + "." for p in parts]
    step = max(1, len(parts) // max_slides)
    slides = [". ".join(parts[i : i + step]) + "." for i in range(0, len(parts), step)]
    return slides[:max_slides]


def _render_slide(title: str, body: str, idx: int, total: int, img_path: str):
    W, H = 1080, 1920
    img = Image.new("RGB", (W, H), (15, 23, 42))
    draw = ImageDraw.Draw(img)

    draw.rounded_rectangle(
        [(64, 220), (W - 64, H - 220)],
        radius=36,
        fill=(30, 41, 59),
        outline=(56, 189, 248),
        width=4,
    )

    f_title = _load_font(52, bold=True)
    f_body = _load_font(46, bold=False)
    f_foot = _load_font(34, bold=False)

    draw.text((112, 290), title.upper()[:30], fill=(56, 189, 248), font=f_title)
    draw.multiline_text(
        (112, 540),
        textwrap.fill(body, width=28),
        fill=(248, 250, 252),
        font=f_body,
        spacing=22,
    )
    draw.text(
        (112, H - 300),
        f"Slide {idx} / {total}  •  AI Reels Studio",
        fill=(148, 163, 184),
        font=f_foot,
    )
    img.save(img_path)


def make_reel_mp4(reel_id: int, title: str, script: str) -> str:
    os.makedirs("outputs", exist_ok=True)
    wav_path = os.path.join("outputs", f"voice_{reel_id}.wav")
    mp4_path = os.path.join("outputs", f"reel_{reel_id}.mp4")

    tts = pyttsx3.init()
    tts.setProperty("rate", 165)
    tts.save_to_file(script, wav_path)
    tts.runAndWait()

    audio = AudioFileClip(wav_path)
    total_dur = max(audio.duration, 6)

    slides = _split_slides(script)
    per_slide = total_dur / len(slides)
    clips = []
    temp_imgs = []

    for i, slide_text in enumerate(slides, start=1):
        img_path = os.path.join("outputs", f"slide_{reel_id}_{i}.png")
        _render_slide(title, slide_text, i, len(slides), img_path)
        temp_imgs.append(img_path)
        base_clip = ImageClip(img_path)
        clip = base_clip.with_duration(per_slide) if _MOVIEPY_V2 else base_clip.set_duration(per_slide)
        clips.append(clip)

    merged = concatenate_videoclips(clips, method="compose")
    final = merged.with_audio(audio) if _MOVIEPY_V2 else merged.set_audio(audio)
    final.write_videofile(mp4_path, fps=24, codec="libx264", audio_codec="aac", logger=None)

    audio.close()
    final.close()
    for p in temp_imgs + [wav_path]:
        if os.path.exists(p):
            os.remove(p)

    return os.path.abspath(mp4_path)