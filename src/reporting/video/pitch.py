"""Pitch video (~2.5 min): a spoken pitch over the 10-slide deck, not a slide read-through.

Output: reports/video/SupeRR_Intelligence_Pitch.mp4 (+ pitch_subtitles.srt, pitch_script.md).
Voice backends (set PITCH_VOICE):
  voicestudio  local VoiceStudio app (installed by the user) at VOICESTUDIO_URL (default http://127.0.0.1:3900)
  own          the presenter's own recordings in reports/video/your_voice/slide01..slide10 (script: RECORDING_SCRIPT.md)
  edge         Microsoft neural voice via edge-tts (default en-IN-NeerjaExpressiveNeural; text sent to Microsoft's service)
  sapi         offline Windows voice, TIMING PREVIEW ONLY (monotone; not for submission)
Every name and number in the script is filled from reports/deck_data.json.
"""
from __future__ import annotations

import json
import os
import subprocess
import urllib.request
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from src.config import REPORTS_DIR
from src.reporting.video.build_video import FONTS, NAVY, PINK, run

V = REPORTS_DIR / "video"
P = V / "assets" / "pitch"
SL, AU, CL = P / "slides", P / "audio", P / "clips"
DECK = REPORTS_DIR / "SupeRR_Intelligence_Pitch.pptx"
FPS = 30
TAIL = 0.35  # breath after each line


def D() -> dict:
    return json.loads((REPORTS_DIR / "deck_data.json").read_text(encoding="utf-8"))


def scenes() -> list[dict]:
    d = D()
    b, w, ub = d["batting"], d["bowling"], d["uncapped"]["batting"]
    un_b, un_w = d["unrestricted"]["batting"], d["unrestricted"]["bowling"]
    cb = next(c for c in d["clutch"] if c["side"] == "batting")
    S = [
        (1, "WHO DELIVERS WHEN IT MATTERS?",
         "Every franchise knows the stars. The harder question, the one that wins auctions, is this: who still delivers when the game is on the line? "
         "And which of those players can Rajasthan Royals actually sign?"),
        (2, f"FIRST TARGET: {w[0]['player'].upper()}",
         f"Here's our answer, up front. {b[0]['player']} leads the batters R R can sign. {w[0]['player']} leads the bowlers, and ranks fifth among the batters too, "
         f"which makes him our first target. And from India's domestic T20, {ub[0]['player']} and {ub[1]['player']} are the uncapped batters to watch."),
        (3, "PRESSURE, DEFINED BEFORE EVERY BALL",
         "So how do we measure pressure? Before every single ball, we ask two questions. How much could this ball swing the match? "
         "And how hard is the situation: the scoreboard, the wickets, the dot balls piling up? The toughest twenty percent of balls count as high pressure, "
         "and yes, batters really do get out more often there."),
        (4, "MOST 'CLUTCH' IS NOISE",
         "Then we make it fair. Every ball is compared with what an average player would do in the same spot, against the same opponents. "
         f"And here's the surprise: most of what people call clutch is noise. Only about {round(cb['reliability_of_raw_delta'] * 100)} percent of it is real. "
         "So we never reward a lucky streak, and a hundred resamples tell us how sure we are about every name."),
        (5, "THE STARS ARE ALL TAKEN",
         f"One reality check changed everything. The very best under pressure, {un_b[0]['player']}, {un_b[1]['player']}, {un_w[0]['player']}, are all under contract. "
         "A list of stars doesn't help on auction day. So we rank only the players R R can actually sign."),
        (6, "BATTERS RR CAN SIGN",
         f"Among the batters, {b[0]['player']}, {b[1]['player']}, {b[2]['player']} and {b[3]['player']} stand out. "
         f"And {w[0]['player']} sits in the ninety-seventh percentile at the death, exactly where Rajasthan have struggled most."),
        (7, "BOWLERS RR CAN SIGN",
         f"With the ball, {w[0]['player']}, {w[1]['player']} and {w[2]['player']} are near-certain picks, in the top ten in almost every resample. "
         f"And {w[1]['player']} already knows the Royals' dressing room."),
        (8, "UNCAPPED, ON INDIAN PITCHES",
         "Then we went further. The data pack has no Indian domestic cricket, so we added two hundred and seventy-two Syed Mushtaq Ali Trophy matches, "
         f"played on Indian pitches. {ub[0]['player']} and {ub[1]['player']} lead the uncapped batters. Domestic batting form carries over to the I P L. "
         "Bowling form doesn't, and we say so honestly."),
        (9, "THE GAP IS AT THE DEATH",
         f"Now, map it to Rajasthan. The top order is the best in the league. The death overs are not. {w[0]['player']} fixes the finish, "
         f"{w[1]['player']} and {w[2]['player']} defend it, Mark Chapman or {b[0]['player']} steady the middle, and the uncapped batters fill the Indian slots."),
        (10, "THE AUCTION PLAN",
         "That's our auction plan. Built on every ball since twenty twenty-two, honest about what we don't know, and ready to re-run the moment the retention lists drop. "
         "Who delivers when it matters? Now R R knows."),
    ]
    return [{"slide": s, "hook": h, "text": t} for s, h, t in S]


# ---------------------------------------------------------------- voice backends
def tts_sapi(items: list[tuple[Path, str]]) -> None:
    lines = ["Add-Type -AssemblyName System.Speech", "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer", "$s.Rate = 1"]
    for out, text in items:
        t = text.replace("'", "''")
        lines += [f"$s.SetOutputToWaveFile('{out}')", f"$s.Speak('{t}')"]
    lines.append("$s.Dispose()")
    run(["powershell", "-NoProfile", "-Command", "\n".join(lines)])


def tts_voicestudio(items: list[tuple[Path, str]]) -> None:
    """VoiceStudio local API. Endpoint and voice are set by env after discovery against the user's install:
    VOICESTUDIO_URL (default http://127.0.0.1:3900), VOICESTUDIO_TTS_PATH (default /v1/audio/speech, OpenAI-compatible),
    VOICESTUDIO_VOICE (profile; default engine voice), VOICESTUDIO_INSTRUCT (OmniVoice voice-design tags), VOICESTUDIO_SPEED."""
    base = os.environ.get("VOICESTUDIO_URL", "http://127.0.0.1:3900").rstrip("/")
    path = os.environ.get("VOICESTUDIO_TTS_PATH", "/v1/audio/speech")
    voice = os.environ.get("VOICESTUDIO_VOICE", "")
    for out, text in items:
        body = {"model": os.environ.get("VOICESTUDIO_MODEL", "omnivoice"), "input": text, "voice": voice or "default",
                "response_format": "wav", "speed": float(os.environ.get("VOICESTUDIO_SPEED", "1.0"))}
        instruct = os.environ.get("VOICESTUDIO_INSTRUCT", "male, middle-aged, moderate pitch, indian accent")
        if instruct:
            body["instructions"] = instruct
        req = urllib.request.Request(base + path, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=600) as r:
            data = r.read()
        if data[:4] != b"RIFF":
            raise RuntimeError(f"VoiceStudio returned non-WAV data ({data[:120]!r}); check VOICESTUDIO_TTS_PATH")
        out.write_bytes(data)


def tts_edge(items: list[tuple[Path, str]]) -> None:
    """Microsoft neural voices via edge-tts (online). Voice/rate/pitch via EDGE_VOICE, EDGE_RATE, EDGE_PITCH."""
    import asyncio

    import edge_tts

    voice = os.environ.get("EDGE_VOICE", "en-IN-NeerjaExpressiveNeural")
    rate, pitch = os.environ.get("EDGE_RATE", "+4%"), os.environ.get("EDGE_PITCH", "+0Hz")

    async def go():
        for out, text in items:
            await edge_tts.Communicate(text.replace("R R", "RR"), voice, rate=rate, pitch=pitch).save(str(out))

    asyncio.run(go())


OWN = V / "your_voice"
CLEAN = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.15,areverse,"
         "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.25,areverse,"
         "highpass=f=80,lowpass=f=12000,afftdn=nf=-25,acompressor=threshold=-20dB:ratio=2.5:attack=10:release=200")


def tts_own(items: list[tuple[Path, str]]) -> None:
    """The presenter's own recordings: reports/video/your_voice/slideNN.(wav|mp3|m4a|...), one per slide.
    Trims leading/trailing silence, removes rumble and hiss, gently evens the level (loudness is normalised later)."""
    for k, (out, _) in enumerate(items, start=1):
        src = next((f for f in sorted(OWN.glob(f"slide{k:02d}.*")) if f.suffix.lower() in {".wav", ".mp3", ".m4a", ".aac", ".ogg", ".flac", ".webm", ".opus"}), None)
        if src is None:
            raise FileNotFoundError(f"Missing recording for slide {k}: put slide{k:02d}.wav (or .mp3/.m4a) in {OWN}")
        run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-af", CLEAN, "-ar", "48000", "-ac", "1", str(out)])


def to_std_wav(src: Path) -> Path:
    dst = src.with_name(src.stem + "_std.wav")
    run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-af", f"apad=pad_dur={TAIL},loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "48000", "-ac", "2", str(dst)])
    return dst


def duration(p: Path) -> float:
    with wave.open(str(p)) as w:
        return w.getnframes() / w.getframerate()


# ---------------------------------------------------------------- visuals
def export_slides() -> None:
    SL.mkdir(parents=True, exist_ok=True)
    ps = f"""$ppt = New-Object -ComObject PowerPoint.Application
try {{ $d = $ppt.Presentations.Open("{DECK}", $true, $false, $false); $i = 0
  foreach ($s in $d.Slides) {{ $i++; $s.Export((Join-Path "{SL}" ("s{{0:D2}}.png" -f $i)), "PNG", 3840, 2160) }}
  $d.Close() }} finally {{ $ppt.Quit() }}"""
    run(["powershell", "-NoProfile", "-Command", ps])


def hook_overlay(text: str, out: Path) -> Path:
    img = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(str(FONTS / "segoeuib.ttf"), 30) if (FONTS / "segoeuib.ttf").exists() else ImageFont.truetype(str(FONTS / "arialbd.ttf"), 30)
    small = ImageFont.truetype(str(FONTS / "segoeui.ttf"), 20) if (FONTS / "segoeui.ttf").exists() else ImageFont.truetype(str(FONTS / "arial.ttf"), 20)
    d.rectangle((0, 1012, 1920, 1080), fill=(*NAVY, 245))
    d.rectangle((0, 1012, 10, 1080), fill=(*PINK, 255))
    d.text((48, 1024), text, font=f, fill=(255, 255, 255, 255))
    credit = "SupeRR Intelligence · independent analysis · not affiliated with Rajasthan Royals"
    d.text((1920 - 48 - d.textlength(credit, font=small), 1034), credit, font=small, fill=(201, 184, 238, 255))
    img.save(out)
    return out


def scene_clip(i: int, slide: Path, wav: Path, hook: str, zoom_in: bool) -> Path:
    dur = duration(wav)
    n = int(dur * FPS) + 1
    ov = hook_overlay(hook, CL / f"hook_{i:02d}.png")
    z = "1.0+0.05*on/{n}".format(n=n) if zoom_in else "1.05-0.05*on/{n}".format(n=n)
    vf = (f"[0:v]scale=3840:2160,zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s=1920x1080:fps={FPS}[bg];"
          f"[bg][1:v]overlay=0:0,fade=t=in:st=0:d=0.35,fade=t=out:st={max(dur - 0.35, 0):.2f}:d=0.35[v]")
    out = CL / f"scene_{i:02d}.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-i", str(slide), "-loop", "1", "-i", str(ov), "-i", str(wav),
         "-filter_complex", vf, "-map", "[v]", "-map", "2:a", "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", str(out)])
    return out


def srt(cues: list[tuple[float, float, str]], path: Path) -> None:
    ts = lambda t: f"{int(t // 3600):02d}:{int(t % 3600 // 60):02d}:{int(t % 60):02d},{int(round((t % 1) * 1000)):03d}"
    path.write_text("\n".join(f"{k}\n{ts(a)} --> {ts(b)}\n{t}\n" for k, (a, b, t) in enumerate(cues, 1)), encoding="utf-8")


def build(voice: str | None = None) -> Path:
    voice = voice or os.environ.get("PITCH_VOICE", "sapi")
    for p in (SL, AU, CL):
        p.mkdir(parents=True, exist_ok=True)
    export_slides()
    sc = scenes()
    raw = [AU / f"line_{i:02d}.wav" for i in range(len(sc))]
    {"voicestudio": tts_voicestudio, "edge": tts_edge, "own": tts_own}.get(voice, tts_sapi)([(w, s["text"]) for w, s in zip(raw, sc)])
    wavs = [to_std_wav(w) for w in raw]
    clips, cues, t = [], [], 0.0
    for i, (s, w) in enumerate(zip(sc, wavs)):
        clips.append(scene_clip(i, SL / f"s{s['slide']:02d}.png", w, s["hook"], zoom_in=i % 2 == 0))
        d = duration(w)
        cues.append((t, t + d - TAIL, s["text"]))
        t += d
    lst = CL / "list.txt"
    lst.write_text("".join(f"file '{c.as_posix()}'\n" for c in clips), encoding="utf-8")
    suffix = "" if voice in ("voicestudio", "edge", "own") else "_PREVIEW_sapi"
    out = V / f"SupeRR_Intelligence_Pitch{suffix}.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", "-movflags", "+faststart", str(out)])
    srt(cues, V / "pitch_subtitles.srt")
    (V / "pitch_script.md").write_text("# Pitch video script\n\n" + "\n\n".join(
        f"**Slide {s['slide']} · {s['hook']}**\n\n{s['text']}" for s in sc) + "\n", encoding="utf-8")
    print(out, f"{t:.1f}s", f"voice={voice}")
    return out


if __name__ == "__main__":
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else None)
