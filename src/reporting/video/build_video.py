"""Render the documentary, trailer and vertical social reel (offline: Windows SAPI narration + FFmpeg).

Outputs in reports/video/: final_documentary.mp4 (chapters + soft subtitles), promotional_trailer.mp4,
social_reel.mp4 (1080x1920, burned captions), subtitles.srt, narration_script.md, chapters.md, thumbnail.png.
Visual assets in reports/video/assets/. Narration is synthetic (Microsoft Zira, offline) and labelled as such.
"""
from __future__ import annotations

import json
import re
import subprocess
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from src.config import REPORTS_DIR
from src.reporting.video import script as SC

V = REPORTS_DIR / "video"
A = V / "assets"
SLIDES, CARDS, AUDIO, CLIPS = A / "slides", A / "cards", A / "audio", A / "clips"
FONTS = Path(r"C:\Windows\Fonts")
NAVY, DEEP, PURPLE, PINK, GOLD, LILAC = (27, 31, 59), (33, 24, 79), (75, 42, 153), (194, 24, 91), (201, 162, 39), (201, 184, 238)
FPS = 30
PAD = 0.45  # seconds of silence after each scene


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / name), size)


def run(cmd: list[str]) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{cmd[0]} failed:\n{r.stderr[-2000:]}")


# ---------------------------------------------------------------- visuals
def export_slides() -> None:
    SLIDES.mkdir(parents=True, exist_ok=True)
    ps = f"""$ppt = New-Object -ComObject PowerPoint.Application
try {{ $d = $ppt.Presentations.Open("{REPORTS_DIR / 'presentation.pptx'}", $true, $false, $false); $i = 0
  foreach ($s in $d.Slides) {{ $i++; $s.Export((Join-Path "{SLIDES}" ("s{{0:D2}}.png" -f $i)), "PNG", 1920, 1080) }}
  $d.Close() }} finally {{ $ppt.Quit() }}"""
    run(["powershell", "-NoProfile", "-Command", ps])


def gradient(w: int, h: int) -> Image.Image:
    img = Image.new("RGB", (w, h), NAVY)
    px = img.load()
    for y in range(h):
        for x in range(0, w, 4):
            t = min(1, (x / w) * 0.7 + (y / h) * 0.5)
            c = tuple(int(NAVY[i] * (1 - t) + DEEP[i] * t * 1.25) for i in range(3))
            for k in range(4):
                if x + k < w:
                    px[x + k, y] = c
    return img


def wrap(draw, text, f, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=f) <= width:
            cur = t
        else:
            lines.append(cur); cur = w
    return lines + [cur] if cur else lines


def chapter_card(n: int, title: str) -> Path:
    img = gradient(1920, 1080)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((140, 380, 300, 540), radius=24, fill=PINK)
    f = font("cambriab.ttf", 96)
    d.text((220, 460), str(n), font=f, fill="white", anchor="mm")
    d.text((350, 395), "CHAPTER", font=font("segoeuib.ttf", 34), fill=GOLD)
    y = 445
    for line in wrap(d, title, font("cambriab.ttf", 76), 1400):
        d.text((350, y), line, font=font("cambriab.ttf", 76), fill="white"); y += 92
    d.text((140, 980), "SupeRR Intelligence · Finding cricket's most reliable players under pressure", font=font("segoeui.ttf", 28), fill=LILAC)
    p = CARDS / f"card_{n:02d}.png"; img.save(p); return p


def end_card() -> Path:
    img = gradient(1920, 1080)
    d = ImageDraw.Draw(img)
    d.text((960, 440), "SupeRR Intelligence", font=font("cambriab.ttf", 110), fill="white", anchor="mm")
    d.text((960, 560), "Pressure-Based Player Reliability & Scouting Engine", font=font("segoeui.ttf", 44), fill=LILAC, anchor="mm")
    d.text((960, 700), "Independent analysis for SupeRR Selector Season 2 · not affiliated with Rajasthan Royals",
           font=font("segoeui.ttf", 30), fill=GOLD, anchor="mm")
    p = CARDS / "card_end.png"; img.save(p); return p


def figure_frame(name: str) -> Path:
    src = Image.open(REPORTS_DIR / "figures" / name).convert("RGB")
    canvas = Image.new("RGB", (1920, 1080), "white")
    src.thumbnail((1760, 920))
    canvas.paste(src, ((1920 - src.width) // 2, (1080 - src.height) // 2))
    p = CARDS / ("fig_" + Path(name).stem + ".png"); canvas.save(p); return p


def visual(v: str) -> Path:
    if v.startswith("card:"):
        k = v.split(":")[1]
        return end_card() if k == "end" else chapter_card(int(k), SC.CHAPTERS[int(k) - 1])
    if v.startswith("fig:"):
        return figure_frame(v.split(":", 1)[1])
    return SLIDES / f"{v}.png"


def thumbnail(top_bat: str, top_bowl: str) -> None:
    img = gradient(1280, 720)
    d = ImageDraw.Draw(img)
    d.text((70, 90), "WHO DELIVERS", font=font("cambriab.ttf", 96), fill="white")
    d.text((70, 195), "UNDER PRESSURE?", font=font("cambriab.ttf", 96), fill=GOLD)
    d.rounded_rectangle((70, 360, 610, 600), radius=22, fill=PURPLE)
    d.rounded_rectangle((660, 360, 1210, 600), radius=22, fill=PINK)
    for x, lab, name in ((100, "#1 BATTER", top_bat), (690, "#1 BOWLER", top_bowl)):
        d.text((x, 385), lab, font=font("segoeuib.ttf", 32), fill=LILAC if x == 100 else "white")
        y = 440
        for line in wrap(d, name, font("cambriab.ttf", 56), 490):
            d.text((x, y), line, font=font("cambriab.ttf", 56), fill="white"); y += 66
    d.text((70, 640), "200,961 balls · IPL + T20I 2022–26 · SupeRR Intelligence documentary", font=font("segoeui.ttf", 28), fill=LILAC)
    img.save(V / "thumbnail.png")


# ---------------------------------------------------------------- audio + subtitles
def tts(items: list[tuple[Path, str]]) -> None:
    AUDIO.mkdir(parents=True, exist_ok=True)
    jobs = AUDIO / "_jobs.json"
    jobs.write_text(json.dumps([{"out": str(p), "text": t} for p, t in items]), encoding="utf-8")
    ps = f"""Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.SelectVoice("Microsoft Zira Desktop"); $s.Rate = -1
$fmt = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(24000, [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen, [System.Speech.AudioFormat.AudioChannel]::Mono)
foreach ($j in (Get-Content -Raw -Encoding UTF8 "{jobs}" | ConvertFrom-Json)) {{
  $s.SetOutputToWaveFile($j.out, $fmt); $s.Speak($j.text) }}
$s.SetOutputToNull(); $s.Dispose()"""
    run(["powershell", "-NoProfile", "-Command", ps])
    jobs.unlink()


def duration(p: Path) -> float:
    with wave.open(str(p)) as w:
        return w.getnframes() / w.getframerate()


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.?!])\s+", text.strip())
    out = []
    for s in parts:  # split long sentences at commas/colons for readable captions
        while len(s) > 110:
            cut = max(s.rfind(", ", 0, 100), s.rfind(": ", 0, 100), s.rfind("; ", 0, 100))
            if cut < 40:
                break
            out.append(s[:cut + 1]); s = s[cut + 2:]
        out.append(s)
    return [s for s in out if s]


def srt_time(t: float) -> str:
    h, m = int(t // 3600), int(t % 3600 // 60)
    s = t % 60
    return f"{h:02d}:{m:02d}:{int(s):02d},{int(round((s % 1) * 1000)):03d}".replace(",1000", ",999")


def cue_list(scenes, durs) -> list[tuple[float, float, str]]:
    cues, t = [], 0.0
    for sc, d in zip(scenes, durs):
        parts = sentences(sc["text"])
        total = sum(len(p) for p in parts)
        st = t
        for p in parts:
            dd = d * len(p) / total
            cues.append((st, st + dd, p)); st += dd
        t += d + PAD
    return cues


def write_srt(cues, path: Path) -> None:
    path.write_text("\n".join(f"{i}\n{srt_time(a)} --> {srt_time(b)}\n{txt}\n" for i, (a, b, txt) in enumerate(cues, 1)), encoding="utf-8")


# ---------------------------------------------------------------- video
def scene_clip(images: list[Path], wav: Path, out: Path, size=(1920, 1080)) -> float:
    d = duration(wav) + PAD
    per = d / len(images)
    inputs, filt = [], []
    for i, im in enumerate(images):
        inputs += ["-loop", "1", "-t", f"{per:.3f}", "-i", str(im)]
        filt.append(f"[{i}:v]scale={size[0]}:{size[1]}:force_original_aspect_ratio=decrease,pad={size[0]}:{size[1]}:(ow-iw)/2:(oh-ih)/2:white,"
                    f"setsar=1,fps={FPS},format=yuv420p,fade=t=in:st=0:d=0.35,fade=t=out:st={max(per - 0.35, 0):.3f}:d=0.35[v{i}]")
    n = len(images)
    filt.append("".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[v]")
    filt.append(f"[{n}:a]apad=pad_dur={PAD},aresample=48000[a]")
    run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-i", str(wav), "-filter_complex", ";".join(filt), "-map", "[v]", "-map", "[a]",
         "-c:v", "libx264", "-preset", "medium", "-tune", "stillimage", "-crf", "20", "-r", str(FPS), "-c:a", "aac", "-b:a", "160k",
         "-ac", "2", "-t", f"{d:.3f}", str(out)])
    return d


def concat(clips: list[Path], out: Path) -> None:
    lst = out.with_suffix(".txt")
    lst.write_text("".join(f"file '{c.as_posix()}'\n" for c in clips), encoding="utf-8")
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out)])
    lst.unlink()


def build(name: str, scenes: list[dict], chapters: bool = False) -> tuple[Path, list, list]:
    CLIPS.mkdir(parents=True, exist_ok=True)
    wavs = [AUDIO / f"{name}_{i:02d}.wav" for i in range(len(scenes))]
    tts([(w, sc["text"]) for w, sc in zip(wavs, scenes)])
    clips, durs = [], []
    for i, (sc, w) in enumerate(zip(scenes, wavs)):
        c = CLIPS / f"{name}_{i:02d}.mp4"
        scene_clip([visual(v) for v in sc["visuals"]], w, c)
        clips.append(c); durs.append(duration(w))
    raw = V / f"_{name}_raw.mp4"
    concat(clips, raw)
    return raw, durs, wavs


def documentary() -> None:
    scenes = SC.documentary()
    raw, durs, _ = build("doc", scenes)
    cues = cue_list(scenes, durs)
    write_srt(cues, V / "subtitles.srt")
    # chapter metadata
    starts, t = {}, 0.0
    for sc, d in zip(scenes, durs):
        starts.setdefault(sc["chapter"], t); t += d + PAD
    total = t
    meta = [";FFMETADATA1", "title=Inside SupeRR Intelligence: Finding Cricket's Most Reliable Players Under Pressure", "artist=SupeRR Intelligence"]
    keys = sorted(starts)
    for i, k in enumerate(keys):
        end = starts[keys[i + 1]] if i + 1 < len(keys) else total
        meta += ["[CHAPTER]", "TIMEBASE=1/1000", f"START={int(starts[k] * 1000)}", f"END={int(end * 1000)}", f"title={k}. {SC.CHAPTERS[k - 1]}"]
    mf = V / "_chapters.txt"; mf.write_text("\n".join(meta) + "\n", encoding="utf-8")
    # Chapters embedded; subtitles ship as sidecar subtitles.srt. (An embedded mov_text track corrupts the
    # MP4 chapter list: QuickTime chapters are themselves a text track.)
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-i", str(mf), "-map", "0:v", "-map", "0:a",
         "-map_metadata", "1", "-map_chapters", "1", "-c", "copy", "-movflags", "+faststart", str(V / "final_documentary.mp4")])
    raw.unlink(); mf.unlink()
    fmt = lambda s: f"{int(s // 60):02d}:{int(s % 60):02d}"
    (V / "chapters.md").write_text("# Documentary chapters\n\n*Inside SupeRR Intelligence: Finding Cricket's Most Reliable Players Under Pressure*. "
                                   f"Total runtime {fmt(total)}.\n\n| Start | Chapter |\n|---|---|\n" +
                                   "".join(f"| {fmt(starts[k])} | {k}. {SC.CHAPTERS[k - 1]} |\n" for k in keys), encoding="utf-8")
    lines = ["# Narration script: Inside SupeRR Intelligence", "",
             "Every number below is generated from pipeline outputs (`src/reporting/video/script.py`). Narration voice: Microsoft Zira (offline Windows speech synthesis, synthetic).", ""]
    cur = None
    for sc in scenes:
        if sc["chapter"] != cur:
            cur = sc["chapter"]; lines += [f"## Chapter {cur}: {SC.CHAPTERS[cur - 1]}", ""]
        if not sc["visuals"][0].startswith("card:"):
            lines += [f"*Visual: {', '.join(sc['visuals'])}*", "", sc["text"], ""]
    (V / "narration_script.md").write_text("\n".join(lines), encoding="utf-8")


def trailer() -> None:
    raw, _, _ = build("trailer", SC.trailer())
    raw.replace(V / "promotional_trailer.mp4")


def reel_frame(slide: Path, hook: str, caption: str, out: Path) -> None:
    img = Image.new("RGB", (1080, 1920), NAVY)
    d = ImageDraw.Draw(img)
    y = 170
    for line in wrap(d, hook, font("cambriab.ttf", 78), 960):
        d.text((540, y), line, font=font("cambriab.ttf", 78), fill=GOLD, anchor="mm"); y += 92
    s = Image.open(slide).convert("RGB"); s.thumbnail((1000, 1000))
    img.paste(s, ((1080 - s.width) // 2, 560))
    d.rounded_rectangle((60, 1240, 1020, 1640), radius=28, fill=DEEP)
    lines = wrap(d, caption, font("segoeuib.ttf", 52), 880)
    yy = 1440 - (len(lines) - 1) * 33
    for line in lines:
        d.text((540, yy), line, font=font("segoeuib.ttf", 52), fill="white", anchor="mm"); yy += 66
    d.text((540, 1800), "SupeRR Intelligence · independent analysis", font=font("segoeui.ttf", 34), fill=LILAC, anchor="mm")
    img.save(out)


def reel() -> None:
    scenes = SC.reel()
    wavs = [AUDIO / f"reel_{i:02d}.wav" for i in range(len(scenes))]
    tts([(w, sc["text"]) for w, sc in zip(wavs, scenes)])
    clips = []
    for i, (sc, w) in enumerate(zip(scenes, wavs)):
        parts = sentences(sc["text"])
        chunks = []
        for p in parts:  # caption chunks of <= ~9 words
            ws = p.split()
            chunks += [" ".join(ws[k:k + 9]) for k in range(0, len(ws), 9)]
        d = duration(w)
        total = sum(len(c) for c in chunks)
        frames = []
        for j, c in enumerate(chunks):
            fp = CLIPS / f"reel_{i:02d}_{j:02d}.png"
            reel_frame(visual(sc["visuals"][0]), sc["hook"], c, fp)
            frames.append((fp, d * len(c) / total + (PAD if j == len(chunks) - 1 else 0)))
        lst = CLIPS / f"reel_{i:02d}.txt"
        lst.write_text("".join(f"file '{f.as_posix()}'\nduration {t:.3f}\n" for f, t in frames) + f"file '{frames[-1][0].as_posix()}'\n", encoding="utf-8")
        c = CLIPS / f"reel_{i:02d}.mp4"
        run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-i", str(w),
             "-filter_complex", f"[0:v]fps={FPS},format=yuv420p,setsar=1[v];[1:a]apad=pad_dur={PAD},aresample=48000[a]",
             "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "20", "-tune", "stillimage", "-c:a", "aac", "-b:a", "160k", "-ac", "2",
             "-t", f"{d + PAD:.3f}", str(c)])
        clips.append(c)
    concat(clips, V / "social_reel.mp4")


def probe(p: Path) -> dict:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height", "-of", "json", str(p)],
                       capture_output=True, text=True)
    return json.loads(r.stdout)


if __name__ == "__main__":
    for d in (SLIDES, CARDS, AUDIO, CLIPS):
        d.mkdir(parents=True, exist_ok=True)
    export_slides()
    D = SC.data()
    thumbnail(D["batting"][0]["player"], D["bowling"][0]["player"])
    documentary()
    trailer()
    reel()
    for f in ("final_documentary.mp4", "promotional_trailer.mp4", "social_reel.mp4"):
        info = probe(V / f)
        print(f, round(float(info["format"]["duration"]), 1), "s", [(s["codec_type"], s.get("width"), s.get("height")) for s in info["streams"]])
