#!/usr/bin/env python3
"""Tự động cắt & dựng video highlight Free Fire từ video quay màn hình.

Cách hoạt động:
  1. Phân tích âm thanh: tiếng súng / nổ là các "xung" năng lượng cao, nhiều tần số cao.
  2. Phân tích chuyển động: khung hình thay đổi mạnh (giao tranh, xoay camera nhanh).
  3. Chấm điểm từng thời điểm, chọn các đoạn "căng" nhất, ghép lại theo thứ tự thời gian.
  4. Dựng: chuyển cảnh chớp trắng, slow-motion khoảnh khắc đỉnh, chữ tiêu đề,
     nhạc nền (tự hạ nhỏ khi có tiếng súng), chuẩn hoá âm lượng, xuất 16:9 hoặc 9:16.

Chỉ cần ffmpeg + numpy.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np

SR = 16000          # sample rate dùng để phân tích
HOP = 0.05          # 50 ms mỗi bước phân tích
MOTION_FPS = 10


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)


def probe(path):
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration:stream=codec_type,width,height,r_frame_rate",
        "-of", "json", path])
    info = json.loads(out)
    dur = float(info["format"]["duration"])
    has_audio = any(s["codec_type"] == "audio" for s in info["streams"])
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    return dur, has_audio, int(v["width"]), int(v["height"])


# ---------------------------------------------------------------- phân tích
def audio_score(path, n):
    raw = subprocess.check_output([
        "ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(SR),
        "-f", "s16le", "-"])
    x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    hop = int(SR * HOP)
    win = hop * 2
    frames = max(1, (len(x) - win) // hop)
    idx = np.arange(win)[None, :] + hop * np.arange(frames)[:, None]
    seg = x[idx] * np.hanning(win)[None, :]
    spec = np.abs(np.fft.rfft(seg, axis=1))
    freqs = np.fft.rfftfreq(win, 1 / SR)
    rms = np.sqrt((seg ** 2).mean(axis=1)) + 1e-9
    hf = spec[:, freqs > 2000].sum(axis=1)              # súng/nổ giàu tần số cao
    flux = np.maximum(0, np.diff(np.log(spec + 1e-6), axis=0)).sum(axis=1)
    flux = np.concatenate([[0], flux])                    # độ "đột ngột"
    loud = 20 * np.log10(rms)
    feat = (norm(flux) * 0.5 + norm(np.log(hf + 1e-6)) * 0.3 + norm(loud) * 0.2)
    return resample(feat, n)


def motion_score(path, n):
    w, h = 64, 36
    raw = subprocess.check_output([
        "ffmpeg", "-v", "error", "-i", path, "-an",
        "-vf", f"fps={MOTION_FPS},scale={w}:{h},format=gray",
        "-f", "rawvideo", "-"])
    f = np.frombuffer(raw, dtype=np.uint8).reshape(-1, h, w).astype(np.float32)
    if len(f) < 2:
        return np.zeros(n)
    d = np.abs(np.diff(f, axis=0)).mean(axis=(1, 2))
    d = np.concatenate([[0], d])
    return resample(norm(d), n)


def norm(a):
    a = np.asarray(a, dtype=np.float32)
    lo, hi = np.percentile(a, 5), np.percentile(a, 99.5)
    return np.clip((a - lo) / (hi - lo + 1e-9), 0, 1)


def resample(a, n):
    if len(a) == n:
        return a
    return np.interp(np.linspace(0, len(a) - 1, n), np.arange(len(a)), a)


def smooth(a, sec):
    k = max(1, int(sec / HOP))
    return np.convolve(a, np.ones(k) / k, mode="same")


def find_highlights(path, target, pre, post, min_gap, verbose=True):
    dur, has_audio, _, _ = probe(path)
    n = int(dur / HOP)
    mot = motion_score(path, n)
    if has_audio:
        aud = audio_score(path, n)
        # mật độ xung âm thanh trong 2s ~ "đấu súng liên tục"
        score = smooth(aud, 2.0) * 0.7 + smooth(mot, 1.0) * 0.3
    else:
        score = smooth(mot, 1.0)
    score = smooth(score, 0.5)

    # Lấy lần lượt các đỉnh cao nhất cho tới khi đủ thời lượng mục tiêu
    s = score.copy()
    picks = []
    total = 0.0
    best = float(score.max())
    while total < target:
        i = int(np.argmax(s))
        if s[i] <= max(0.1, best * 0.5):   # không còn gì đáng xem
            break
        t = i * HOP
        a, b = max(0, t - pre), min(dur, t + post)
        if picks and total + (b - a) > target * 1.1:
            break
        picks.append([a, b, float(score[i]), t])
        total += b - a
        lo, hi = max(0, int((a - min_gap) / HOP)), min(n, int((b + min_gap) / HOP))
        s[lo:hi] = 0
    picks.sort()
    merged = []
    for p in picks:
        if merged and p[0] - merged[-1][1] < min_gap:
            m = merged[-1]
            m[1] = max(m[1], p[1])
            if p[2] > m[2]:
                m[2], m[3] = p[2], p[3]
        else:
            merged.append(p)
    if verbose:
        print(f"Video dài {dur:.1f}s, âm thanh: {'có' if has_audio else 'không'}")
        for k, (a, b, sc, pk) in enumerate(merged, 1):
            print(f"  #{k}: {fmt(a)} → {fmt(b)}  (đỉnh {fmt(pk)}, điểm {sc:.2f})")
    return merged, has_audio


def fmt(t):
    return f"{int(t // 60):02d}:{t % 60:05.2f}"


# ---------------------------------------------------------------- dựng video
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf",
]


def font():
    for f in FONT_CANDIDATES:
        if os.path.exists(f):
            return f
    return None


def esc(text):
    return text.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’")


def frame_filter(W, H, vertical):
    if vertical:
        # nền mờ + video gốc ở giữa (kiểu TikTok/Shorts)
        return (f"split[bg][fg];"
                f"[bg]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                f"boxblur=20:2,eq=brightness=-0.15[bg2];"
                f"[fg]scale={W}:-2[fg2];[bg2][fg2]overlay=(W-w)/2:(H-h)/2")
    return (f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
            f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2")


def render_clip(src, a, b, peak, out, W, H, fps, vertical, slowmo, has_audio):
    """Cắt 1 đoạn, chuẩn hoá khung hình; slow-motion 1s quanh đỉnh."""
    d = b - a
    pk = min(max(peak - a, 0.6), d - 0.6)
    vf_base = frame_filter(W, H, vertical)
    inputs = ["-ss", f"{a:.3f}", "-t", f"{d:.3f}", "-i", src]
    if not has_audio:
        inputs += ["-f", "lavfi", "-t", f"{d:.3f}", "-i", f"anullsrc=r=48000:cl=stereo"]
    ain = "1:a" if not has_audio else "0:a"
    if slowmo and d > 2.5:
        s0, s1 = pk - 0.5, pk + 0.5
        fc = (
            f"[0:v]fps={fps},{vf_base},split=3[v0][v1][v2];"
            f"[v0]trim=0:{s0:.3f},setpts=PTS-STARTPTS[va];"
            f"[v1]trim={s0:.3f}:{s1:.3f},setpts=2*(PTS-STARTPTS),"
            f"eq=saturation=1.3:contrast=1.08[vb];"
            f"[v2]trim={s1:.3f},setpts=PTS-STARTPTS[vc];"
            f"[{ain}]aresample=48000,aformat=channel_layouts=stereo,asplit=3[a0][a1][a2];"
            f"[a0]atrim=0:{s0:.3f},asetpts=PTS-STARTPTS[aa];"
            f"[a1]atrim={s0:.3f}:{s1:.3f},asetpts=PTS-STARTPTS,atempo=0.5[ab];"
            f"[a2]atrim={s1:.3f},asetpts=PTS-STARTPTS[ac];"
            f"[va][aa][vb][ab][vc][ac]concat=n=3:v=1:a=1[v][a]")
    else:
        fc = (f"[0:v]fps={fps},{vf_base}[v];"
              f"[{ain}]aresample=48000,aformat=channel_layouts=stereo[a]")
    run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc,
         "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast",
         "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", out])
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=nw=1:nk=1", out]))


def assemble(clips, durs, out, W, H, title, music, trans, music_vol, caption=None):
    T = trans
    args = ["ffmpeg", "-v", "error", "-y"]
    for c in clips:
        args += ["-i", c]
    fc = []
    n = len(clips)
    # chuỗi xfade (chớp trắng) + acrossfade
    if n == 1:
        fc.append("[0:v]null[vx];[0:a]anull[ax]")
        total = durs[0]
    elif T <= 0:
        fc.append("".join(f"[{i}:v][{i}:a]" for i in range(n)) +
                  f"concat=n={n}:v=1:a=1[vx][ax]")
        total = sum(durs)
    else:
        prev_v, prev_a = "[0:v]", "[0:a]"
        acc = durs[0]
        for i in range(1, n):
            off = acc - T
            fc.append(f"{prev_v}[{i}:v]xfade=transition=fadewhite:duration={T}:"
                      f"offset={off:.3f}[v{i}]")
            fc.append(f"{prev_a}[{i}:a]acrossfade=d={T}[a{i}]")
            prev_v, prev_a = f"[v{i}]", f"[a{i}]"
            acc = acc + durs[i] - T
        fc.append(f"{prev_v}null[vx];{prev_a}anull[ax]")
        total = acc
    # tiêu đề + fade in/out
    vchain = f"[vx]fade=t=in:st=0:d=0.4,fade=t=out:st={max(0, total - 0.8):.3f}:d=0.8"
    f = font()
    if title and f:
        fs = int(W * 0.07)
        vchain += (f",drawtext=fontfile={f}:text='{esc(title)}':fontsize={fs}:"
                   f"fontcolor=white:borderw=6:bordercolor=black:"
                   f"x=(w-text_w)/2:y=h*0.12:enable='between(t,0.3,3.0)':"
                   f"alpha='if(lt(t,0.6),(t-0.3)/0.3,if(gt(t,2.6),(3.0-t)/0.4,1))'")
    if caption and f:
        cs = int(W * 0.055)
        lines = caption.split("|")
        for li, line in enumerate(lines):
            vchain += (f",drawtext=fontfile={f}:text='{esc(line)}':fontsize={cs}:"
                       f"fontcolor=white:borderw=5:bordercolor=black:box=0:"
                       f"x=(w-text_w)/2:y=h*0.06+{li}*{int(cs * 1.25)}")
    fc.append(vchain + "[vout]")
    if music:
        args += ["-stream_loop", "-1", "-i", music]
        mi = n
        fc.append(f"[ax]loudnorm=I=-16:TP=-1.5,asplit=2[game][sc]")
        fc.append(f"[{mi}:a]aresample=48000,aformat=channel_layouts=stereo,"
                  f"volume={music_vol},atrim=0:{total:.3f}[mus]")
        # nhạc tự nhỏ lại khi có tiếng súng
        fc.append("[mus][sc]sidechaincompress=threshold=0.05:ratio=6:attack=20:release=400[duck]")
        fc.append(f"[game][duck]amix=inputs=2:duration=first:normalize=0,"
                  f"afade=t=out:st={max(0, total - 1):.3f}:d=1[aout]")
    else:
        fc.append(f"[ax]loudnorm=I=-16:TP=-1.5,afade=t=out:st={max(0, total - 1):.3f}:d=1[aout]")
    args += ["-filter_complex", ";".join(fc), "-map", "[vout]", "-map", "[aout]",
             "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
    run(args)
    return total


# ---------------------------------------------------------------- chế độ kể chuyện
def atempo_chain(sp):
    parts = []
    while sp > 2.0:
        parts.append("atempo=2.0"); sp /= 2.0
    while sp < 0.5:
        parts.append("atempo=0.5"); sp /= 0.5
    parts.append(f"atempo={sp:.4f}")
    return ",".join(parts)


def story_plan(src, t0, t1, target):
    """Giữ liền mạch đoạn [t0,t1]; đoạn giao tranh tốc độ thường, đoạn nhàn tua nhanh."""
    dur, has_audio, _, _ = probe(src)
    t1 = min(t1, dur)
    n = int(dur / HOP)
    mot = motion_score(src, n)
    sc = (smooth(audio_score(src, n), 2.0) * 0.7 + smooth(mot, 1.0) * 0.3) if has_audio \
        else smooth(mot, 1.0)
    sc = smooth(sc, 1.0)
    i0, i1 = int(t0 / HOP), int(t1 / HOP)
    rs = sc[i0:i1]
    thr = max(0.1, np.percentile(rs, 60), rs.max() * 0.45)
    act = rs > thr
    # nới vùng giao tranh ra 2s trước / 1s sau cho đủ bối cảnh
    k_pre, k_post = int(2.0 / HOP), int(1.0 / HOP)
    idx = np.where(act)[0]
    grown = np.zeros_like(act)
    for i in idx:
        grown[max(0, i - k_pre):i + k_post] = True
    # gom thành các khối liên tiếp
    runs, start = [], 0
    for i in range(1, len(grown) + 1):
        if i == len(grown) or grown[i] != grown[start]:
            runs.append([t0 + start * HOP, t0 + i * HOP, bool(grown[start])])
            start = i
    # bỏ khối quá ngắn (<1.5s) bằng cách gộp vào khối trước
    clean = []
    for r in runs:
        if clean and (r[1] - r[0] < 1.5 or clean[-1][1] - clean[-1][0] < 1.5):
            clean[-1][1] = r[1]
            clean[-1][2] = clean[-1][2] or r[2]
        else:
            clean.append(r)
    A = sum(b - a for a, b, x in clean if x)
    C = sum(b - a for a, b, x in clean if not x)
    target = target - 0.5 * sum(1 for r in clean if r[2])   # chừa chỗ cho slow-mo
    if A + C <= target:
        calm_sp, act_sp = 1.0, 1.0
    elif A < target * 0.8:
        calm_sp, act_sp = min(4.0, C / max(0.1, target - A)), 1.0
        if A + C / calm_sp > target:          # tua tối đa vẫn dài -> tua nhẹ cả giao tranh
            act_sp = A / max(0.1, target - C / calm_sp)
    else:
        calm_sp = 4.0
        act_sp = (A) / max(0.1, target - C / calm_sp)
    act_sp = max(1.0, act_sp)
    # đỉnh của mỗi khối giao tranh (để slow-mo)
    plan = []
    for a, b, x in clean:
        sp = act_sp if x else calm_sp
        j0, j1 = int(a / HOP), max(int(a / HOP) + 1, int(b / HOP))
        pk = (j0 + int(np.argmax(sc[j0:j1]))) * HOP
        plan.append((a, b, sp, x, pk))
    print(f"Đoạn {fmt(t0)}–{fmt(t1)}: giao tranh {A:.0f}s, nhàn {C:.0f}s "
          f"→ tua giao tranh x{act_sp:.2f}, đoạn nhàn x{calm_sp:.2f}")
    for a, b, sp, x, pk in plan:
        print(f"  {fmt(a)}–{fmt(b)}  {'GIAO TRANH' if x else 'tua      '} x{sp:.2f}")
    return plan, has_audio


def render_story_piece(src, a, b, sp, action, peak, out, W, H, fps, vertical,
                       has_audio, slowmo):
    d = b - a
    vf_base = frame_filter(W, H, vertical)
    inputs = ["-ss", f"{a:.3f}", "-t", f"{d:.3f}", "-i", src]
    if not has_audio:
        inputs += ["-f", "lavfi", "-t", f"{d:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
    ain = "0:a" if has_audio else "1:a"
    label = ""
    f = font()
    if sp > 1.05 and f:
        fs = int(W * 0.045)
        label = (f",drawtext=fontfile={f}:text='▶▶ x{sp:.1f}':fontsize={fs}:fontcolor=white:"
                 f"borderw=4:bordercolor=black:x=w-text_w-40:y=h-text_h-60")
        if "▶" in label:
            label = label.replace("▶▶ ", ">> ")
    aformat = "aresample=48000,aformat=channel_layouts=stereo"
    if action and slowmo and d > 3 and sp <= 1.05:
        pk = min(max(peak - a, 0.6), d - 0.6)
        s0, s1 = pk - 0.5, pk + 0.5
        fc = (f"[0:v]fps={fps},{vf_base},split=3[v0][v1][v2];"
              f"[v0]trim=0:{s0:.3f},setpts=PTS-STARTPTS[va];"
              f"[v1]trim={s0:.3f}:{s1:.3f},setpts=2*(PTS-STARTPTS),eq=saturation=1.3:contrast=1.08[vb];"
              f"[v2]trim={s1:.3f},setpts=PTS-STARTPTS[vc];"
              f"[{ain}]{aformat},asplit=3[a0][a1][a2];"
              f"[a0]atrim=0:{s0:.3f},asetpts=PTS-STARTPTS[aa];"
              f"[a1]atrim={s0:.3f}:{s1:.3f},asetpts=PTS-STARTPTS,atempo=0.5[ab];"
              f"[a2]atrim={s1:.3f},asetpts=PTS-STARTPTS[ac];"
              f"[va][aa][vb][ab][vc][ac]concat=n=3:v=1:a=1[v][a]")
    else:
        fc = (f"[0:v]setpts=PTS/{sp:.4f},fps={fps},{vf_base}{label}[v];"
              f"[{ain}]{aformat},{atempo_chain(sp)}[a]")
    run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc,
         "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast",
         "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", out])
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=nw=1:nk=1", out]))


def main():
    ap = argparse.ArgumentParser(description="Tự động dựng highlight Free Fire")
    ap.add_argument("inputs", nargs="+", help="video quay màn hình (1 hoặc nhiều file)")
    ap.add_argument("-o", "--output", default="highlight.mp4")
    ap.add_argument("--length", type=float, default=60, help="tổng thời lượng mục tiêu (giây)")
    ap.add_argument("--pre", type=float, default=4.0, help="giây lấy trước khoảnh khắc đỉnh")
    ap.add_argument("--post", type=float, default=2.0, help="giây lấy sau khoảnh khắc đỉnh")
    ap.add_argument("--gap", type=float, default=2.0, help="gộp các đoạn cách nhau < gap giây")
    ap.add_argument("--vertical", action="store_true", help="xuất 9:16 cho TikTok/Shorts/Reels")
    ap.add_argument("--no-slowmo", action="store_true")
    ap.add_argument("--title", default="FREE FIRE HIGHLIGHT")
    ap.add_argument("--music", help="file nhạc nền (mp3/m4a...)")
    ap.add_argument("--music-vol", type=float, default=0.35)
    ap.add_argument("--fps", type=int, default=60)
    ap.add_argument("--analyze", action="store_true", help="chỉ in các đoạn phát hiện, không dựng")
    ap.add_argument("--segments", help='tự chọn đoạn, vd "00:12-00:20,01:05-01:15"')
    ap.add_argument("--story", help='chế độ kể chuyện: giữ liền mạch đoạn "mm:ss-mm:ss", '
                    'tua nhanh đoạn nhàn để vừa --length')
    ap.add_argument("--caption", help='chữ cố định suốt video, dùng | để xuống dòng')
    a = ap.parse_args()

    if a.story:
        W, H = (1080, 1920) if a.vertical else (1920, 1080)
        src = a.inputs[0]
        t0, t1 = (parse_t(x) for x in a.story.split("-"))
        plan, has_audio = story_plan(src, t0, t1, a.length)
        if a.analyze:
            return
        tmp = tempfile.mkdtemp(prefix="ffhl_")
        try:
            clips, durs = [], []
            for k, (s0, s1, sp, x, pk) in enumerate(plan):
                out = os.path.join(tmp, f"s{k:03d}.mp4")
                print(f"Dựng khối {k + 1}/{len(plan)}")
                durs.append(render_story_piece(src, s0, s1, sp, x, pk, out, W, H, a.fps,
                                               a.vertical, has_audio, not a.no_slowmo))
                clips.append(out)
            total = assemble(clips, durs, a.output, W, H, a.title, a.music, 0,
                             a.music_vol, a.caption)
            print(f"\nXong! {a.output} ({total:.1f}s, {W}x{H})")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        return

    W, H = (1080, 1920) if a.vertical else (1920, 1080)
    plan = []  # (src, start, end, peak, has_audio)
    per_file = a.length / len(a.inputs)
    for src in a.inputs:
        print(f"\n== Phân tích {src}")
        if a.segments:
            _, has_audio, _, _ = probe(src)
            for part in a.segments.split(","):
                s, e = (parse_t(x) for x in part.split("-"))
                plan.append((src, s, e, (s + e) / 2 + (e - s) * 0.2, has_audio))
        else:
            segs, has_audio = find_highlights(src, per_file, a.pre, a.post, a.gap)
            plan += [(src, s, e, pk, has_audio) for s, e, _, pk in segs]
    if not plan:
        sys.exit("Không tìm thấy đoạn nào đáng chú ý.")
    if a.analyze:
        return

    tmp = tempfile.mkdtemp(prefix="ffhl_")
    try:
        clips, durs = [], []
        for k, (src, s, e, pk, ha) in enumerate(plan):
            out = os.path.join(tmp, f"c{k:03d}.mp4")
            print(f"Dựng đoạn {k + 1}/{len(plan)} ({fmt(s)}–{fmt(e)})")
            durs.append(render_clip(src, s, e, pk, out, W, H, a.fps, a.vertical,
                                    not a.no_slowmo, ha))
            clips.append(out)
        trans = min(0.35, min(durs) / 3)
        total = assemble(clips, durs, a.output, W, H, a.title, a.music, trans, a.music_vol)
        print(f"\nXong! {a.output} ({total:.1f}s, {W}x{H})")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def parse_t(s):
    s = s.strip()
    parts = [float(p) for p in s.split(":")]
    t = 0.0
    for p in parts:
        t = t * 60 + p
    return t


if __name__ == "__main__":
    main()
