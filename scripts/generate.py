#!/usr/bin/env python3
"""Generate static site for AI Daily Report from JSON data."""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path.home() / "daily-report-site"
DATA_DIR = BASE / "data"
AUDIO_DIR = BASE / "audio"
OUTPUT_DIR = BASE / "output"
TEMPLATE_FILE = BASE / "templates" / "template.html"

AUDIO_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_reports():
    reports = {}
    for f in sorted(DATA_DIR.glob("*.json")):
        with open(f) as fh:
            r = json.load(fh)
            reports[r["date"]] = r
    return reports

def build_tts_text(report):
    """Build TTS text from report content."""
    date_part = report['title'].replace('AI 早报 | ', '')
    lines = [f"AI早报，{date_part}。"]
    lines.append("")
    lines.append(f"头条：{report['headline_title']}")
    lines.append(report['headline_body'])
    if report.get('headline_comment'):
        lines.append(f"小咪说：{report['headline_comment']}")
    lines.append("")
    
    for s in report.get('sections', []):
        lines.append(f"{s['name']}：{s['content']}")
        lines.append("")
    
    if report.get('daily_insight'):
        lines.append(f"今日观察：{report['daily_insight']}")
    
    return "\n".join(lines)

def generate_audio(report):
    """Generate TTS audio for a report if it doesn't exist."""
    audio_path = AUDIO_DIR / f"{report['date']}.mp3"
    if audio_path.exists() and audio_path.stat().st_size > 1000:
        report["audio_file"] = f"audio/{report['date']}.mp3"
        return True
    
    text = build_tts_text(report)
    
    try:
        import edge_tts
        import asyncio
        
        async def _gen():
            communicate = edge_tts.Communicate(text[:5000], "zh-CN-XiaoxiaoNeural")
            await communicate.save(str(audio_path))
        
        asyncio.run(_gen())
        
        if audio_path.exists() and audio_path.stat().st_size > 1000:
            report["audio_file"] = f"audio/{report['date']}.mp3"
            print(f"  ✓ Audio: {audio_path.name} ({audio_path.stat().st_size/1024:.0f}KB)")
            return True
        else:
            print(f"  ✗ Audio generation failed (file too small or missing)")
            return False
    except Exception as e:
        print(f"  ✗ Audio generation error: {e}")
        return False

def build_site(reports):
    """Generate all HTML files from template."""
    with open(TEMPLATE_FILE) as f:
        template = f.read()
    
    # Sort reports by date (newest first)
    sorted_dates = sorted(reports.keys(), reverse=True)
    
    # Serialize reports data for JS injection
    reports_json = json.dumps(reports, ensure_ascii=False, indent=2)
    
    # Replace placeholder with actual data
    site_html = template.replace("__REPORTS_DATA__;", reports_json + ";")
    
    # Generate index.html
    index_path = OUTPUT_DIR / "index.html"
    with open(index_path, "w") as f:
        f.write(site_html)
    print(f"  ✓ index.html generated")
    
    # Generate per-date HTML files (for direct URL access and SEO)
    for date in sorted_dates:
        page_path = OUTPUT_DIR / f"{date}.html"
        with open(page_path, "w") as f:
            f.write(site_html)
    
    print(f"  ✓ {len(sorted_dates)} daily pages generated")
    
    # Copy audio files to output
    audio_output = OUTPUT_DIR / "audio"
    audio_output.mkdir(exist_ok=True)
    for date in sorted_dates:
        r = reports[date]
        if r.get("audio_file"):
            src = AUDIO_DIR / f"{date}.mp3"
            if src.exists():
                dst = audio_output / f"{date}.mp3"
                if not dst.exists():
                    import shutil
                    shutil.copy2(src, dst)
    
    print(f"  ✓ Audio files copied")

def main():
    print("=" * 50)
    print("AI Daily Report · Site Generator")
    print(f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 50)
    
    reports = load_reports()
    print(f"\n📄 Loaded {len(reports)} reports:")
    for date in sorted(reports.keys(), reverse=True):
        r = reports[date]
        audio_status = "🔊" if r.get("audio_file") else "⏳"
        print(f"  {date} - {r['title']} {audio_status}")
    
    # Generate missing audio
    print("\n🎤 Generating audio...")
    for date in sorted(reports.keys(), reverse=True):
        r = reports[date]
        if not r.get("audio_file"):
            generate_audio(r)
    
    # Build site
    print("\n🏗️  Building site...")
    build_site(reports)
    
    print("\n✅ Done! Open:")
    print(f"   file://{OUTPUT_DIR}/index.html")

if __name__ == "__main__":
    main()
