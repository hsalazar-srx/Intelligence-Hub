#!/usr/bin/env python3
"""
IT Strategy Intelligence Hub — YouTube Signal Tracker
──────────────────────────────────────────────────────
Runs weekly via GitHub Actions. For each curated channel:
  1. Checks RSS feed for new videos since last run
  2. Fetches transcript (no API key needed)
  3. Sends to Claude API for relevance filtering
  4. If relevant → creates draft signal .md and opens a GitHub PR

Environment variables required:
  ANTHROPIC_API_KEY   — from repo secrets
  GITHUB_TOKEN        — auto-provided by Actions
  GITHUB_REPOSITORY   — auto-provided by Actions (owner/repo)
"""

import os, re, json, yaml, requests, datetime, textwrap, time
from pathlib import Path
from xml.etree import ElementTree as ET
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
import anthropic

# ── Config ────────────────────────────────────────────────────
ROOT          = Path(__file__).parent.parent
CHANNELS_FILE = ROOT / "channels.yml"
STATE_FILE    = ROOT / ".github" / "yt-state.json"
DRAFTS_DIR    = ROOT / "signals" / "drafts"
DRAFTS_DIR.mkdir(parents=True, exist_ok=True)

GITHUB_REPO   = os.environ.get("GITHUB_REPOSITORY", "")
GITHUB_TOKEN  = os.environ.get("GITHUB_TOKEN", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

GITHUB_API    = "https://api.github.com"
HEADERS       = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}

# Max transcript characters to send to Claude (keeps costs low)
TRANSCRIPT_CHARS = 8000

# ── Relevance filter system prompt ────────────────────────────
SYSTEM_PROMPT = """You are a signal filter for a manufacturing IT team at a mid-size industrial company.
The team is building an AI Platform on top of Infor M3/MOVEX ERP and a modernized MES (Manufacturing Execution System).
Active projects: digital-transformation, ai-platform, m3-erp-integration.

RELEVANT signals cover (medium bar — enterprise AI broadly):
- Enterprise AI deployment: RAG, agents, evals, MLOps, LLMOps in production
- System integration patterns: ERP, MES, event-driven architecture, API design at scale
- AI platform architecture for established (non-startup) organisations
- Data architecture for AI: pipelines, vector stores, data governance
- Change management and organisational readiness for technology transformation
- LLM deployment in regulated, operational, or industrial environments
- Practical prompt engineering and AI workflow design
- Security and governance for AI systems

DISCARD if primarily about:
- Greenfield startups / consumer products built from scratch
- Consumer AI tips (personal ChatGPT usage, Copilot for individuals)
- Pure academic ML research with no production deployment angle
- Crypto / Web3 unless explicitly about enterprise data ownership
- Vibe coding, no-code hobby projects, influencer motivation content
- Gaming AI, art generation for personal use

If RELEVANT, return ONLY valid JSON (no markdown, no explanation):
{
  "relevant": true,
  "title": "Concise signal title (max 80 chars)",
  "project": "ai-platform|digital-transformation|m3-erp-integration",
  "relevance": "high|medium",
  "tags": ["tag1", "tag2", "tag3"],
  "what": "1-2 sentences: what does this video cover?",
  "why": "2-3 sentences: why does this matter to our manufacturing IT / AI platform context specifically?",
  "action": "One concrete next action, decision, or question this enables for the team"
}

If NOT relevant, return ONLY: {"relevant": false}"""

# ── Load / save state ─────────────────────────────────────────
def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"processed_video_ids": [], "last_run": None}

def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))

# ── YouTube RSS ───────────────────────────────────────────────
def fetch_channel_videos(channel_id):
    """Returns list of {id, title, published, url} dicts, newest first."""
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"    ⚠️  RSS fetch failed for {channel_id}: {e}")
        return []

    ns = {
        'atom': 'http://www.w3.org/2005/Atom',
        'yt':   'http://www.youtube.com/xml/schemas/2015',
        'media':'http://search.yahoo.com/mrss/'
    }
    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError as e:
        print(f"    ⚠️  XML parse error for {channel_id}: {e}")
        return []

    videos = []
    for entry in root.findall('atom:entry', ns):
        vid_id   = entry.findtext('yt:videoId', namespaces=ns)
        title    = entry.findtext('atom:title', namespaces=ns)
        pub      = entry.findtext('atom:published', namespaces=ns)
        if vid_id and title:
            videos.append({
                'id':        vid_id,
                'title':     title,
                'published': pub or '',
                'url':       f"https://www.youtube.com/watch?v={vid_id}"
            })
    return videos

# ── Transcript fetch ──────────────────────────────────────────
def fetch_transcript(video_id):
    """Returns transcript text or None if unavailable."""
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'en-US', 'en-GB'])
        text = ' '.join(seg['text'] for seg in transcript)
        return text[:TRANSCRIPT_CHARS]
    except (NoTranscriptFound, TranscriptsDisabled):
        return None
    except Exception as e:
        print(f"      ⚠️  Transcript error: {e}")
        return None

# ── Claude relevance filter ───────────────────────────────────
def filter_with_claude(video, channel, transcript):
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

    user_content = f"""Channel: {channel['name']} (hint: {channel.get('project_hint', 'general')})
Video title: {video['title']}
Video URL: {video['url']}
Published: {video['published']}

Transcript excerpt:
{transcript or '[No transcript available — evaluate from title only]'}"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=600,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}]
        )
        raw = message.content[0].text.strip()
        # Strip any accidental markdown fences
        raw = re.sub(r'^```json\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"      ⚠️  Claude returned invalid JSON: {e}")
        return {"relevant": False}
    except Exception as e:
        print(f"      ⚠️  Claude API error: {e}")
        return {"relevant": False}

# ── Signal markdown generator ─────────────────────────────────
def generate_signal_md(video, channel, signal_data):
    today = datetime.date.today().isoformat()
    slug  = re.sub(r'[^a-z0-9]+', '-', signal_data['title'].lower()).strip('-')[:60]
    filename = f"{today}-{slug}.md"

    tags_yaml = ', '.join(f'"{t}"' for t in signal_data.get('tags', []))

    content = f"""---
date: {today}
title: "{signal_data['title']}"
source: "YouTube: {channel['name']}"
topic: "{', '.join(signal_data.get('tags', []))}"
tags: [{tags_yaml}]
project: {signal_data.get('project', channel.get('project_hint', 'general'))}
relevance: {signal_data.get('relevance', 'medium')}
video_url: "{video['url']}"
auto_generated: true
---

## Signal: {signal_data['title']}

### What I read / watched
{signal_data.get('what', '')}

### Why it matters to MY context
{signal_data.get('why', '')}

### Action / Decision implication
- [ ] {signal_data.get('action', 'Review and determine relevance to current sprint')}

### Links
- Source: [{channel['name']} — YouTube]({video['url']})
- Channel: {channel['name']}

---
*Auto-generated by YouTube Signal Tracker · {today} · Review before merging*
"""
    return filename, content

# ── GitHub PR creator ─────────────────────────────────────────
def get_default_branch():
    resp = requests.get(f"{GITHUB_API}/repos/{GITHUB_REPO}", headers=HEADERS, timeout=10)
    return resp.json().get("default_branch", "main")

def get_branch_sha(branch):
    resp = requests.get(f"{GITHUB_API}/repos/{GITHUB_REPO}/git/ref/heads/{branch}", headers=HEADERS, timeout=10)
    return resp.json()["object"]["sha"]

def create_pr(filename, content, video, channel, signal_data):
    default_branch = get_default_branch()
    base_sha       = get_branch_sha(default_branch)
    today          = datetime.date.today().isoformat()
    branch_name    = f"signal/yt-{today}-{filename.replace('.md','')[:40]}"

    # 1. Create branch
    r = requests.post(f"{GITHUB_API}/repos/{GITHUB_REPO}/git/refs", headers=HEADERS, timeout=10,
        json={"ref": f"refs/heads/{branch_name}", "sha": base_sha})
    if r.status_code not in (201, 422):  # 422 = branch exists
        print(f"      ⚠️  Failed to create branch: {r.status_code} {r.text[:200]}")
        return False

    # 2. Create file on branch
    file_path = f"signals/drafts/{filename}"
    import base64
    encoded   = base64.b64encode(content.encode()).decode()
    r = requests.put(f"{GITHUB_API}/repos/{GITHUB_REPO}/contents/{file_path}",
        headers=HEADERS, timeout=10,
        json={
            "message": f"signal: {signal_data['title'][:72]}",
            "content": encoded,
            "branch":  branch_name
        })
    if r.status_code not in (200, 201):
        print(f"      ⚠️  Failed to create file: {r.status_code} {r.text[:200]}")
        return False

    # 3. Open Pull Request
    relevance_emoji = "🔴" if signal_data.get('relevance') == 'high' else "🟡"
    pr_body = f"""## 📺 Auto-generated signal from YouTube

**Channel:** {channel['name']}
**Video:** [{video['title']}]({video['url']})
**Relevance:** {relevance_emoji} {signal_data.get('relevance', 'medium').upper()}
**Project:** `{signal_data.get('project', 'general')}`

### Extracted signal

**Why it matters:**
{signal_data.get('why', '')}

**Suggested action:**
{signal_data.get('action', '')}

---
**To publish:** Review the signal content in `signals/drafts/{filename}`, edit if needed, then merge this PR.
**To discard:** Close this PR without merging.

*Generated by YouTube Signal Tracker · {today}*"""

    r = requests.post(f"{GITHUB_API}/repos/{GITHUB_REPO}/pulls", headers=HEADERS, timeout=10,
        json={
            "title": f"[Signal] {relevance_emoji} {signal_data['title'][:80]}",
            "body":  pr_body,
            "head":  branch_name,
            "base":  default_branch,
            "draft": False
        })
    if r.status_code == 201:
        pr_url = r.json().get('html_url', '')
        print(f"      ✅ PR opened: {pr_url}")
        return True
    else:
        print(f"      ⚠️  Failed to open PR: {r.status_code} {r.text[:200]}")
        return False

# ── Main ──────────────────────────────────────────────────────
def main():
    print("📺 YouTube Signal Tracker starting...")
    print(f"   Repository: {GITHUB_REPO}")
    print(f"   Timestamp:  {datetime.datetime.utcnow().isoformat()}Z\n")

    if not ANTHROPIC_KEY:
        print("❌ ANTHROPIC_API_KEY not set. Add it to GitHub repo secrets.")
        return
    if not GITHUB_TOKEN:
        print("❌ GITHUB_TOKEN not available.")
        return

    # Load channels
    if not CHANNELS_FILE.exists():
        print(f"❌ channels.yml not found at {CHANNELS_FILE}")
        return
    channels = yaml.safe_load(CHANNELS_FILE.read_text()).get('channels', [])
    print(f"📋 Loaded {len(channels)} channels\n")

    # Load processed state
    state = load_state()
    processed_ids = set(state.get('processed_video_ids', []))
    new_processed  = []
    signals_created = 0

    for channel in channels:
        name       = channel.get('name', 'Unknown')
        channel_id = channel.get('channel_id', '')
        priority   = channel.get('priority', 'medium')

        print(f"🔍 {name} [{priority}]")

        if not channel_id:
            print(f"   ⚠️  No channel_id — skipping")
            continue

        videos = fetch_channel_videos(channel_id)
        new_videos = [v for v in videos if v['id'] not in processed_ids]

        if not new_videos:
            print(f"   ✓ No new videos")
            continue

        print(f"   Found {len(new_videos)} new video(s)")

        for video in new_videos[:3]:  # Process max 3 new videos per channel per run
            vid_id = video['id']
            print(f"   📹 {video['title'][:70]}")

            # Fetch transcript
            transcript = fetch_transcript(vid_id)
            if transcript:
                print(f"      📝 Transcript: {len(transcript)} chars")
            else:
                print(f"      📝 No transcript — filtering on title only")

            # Filter with Claude
            print(f"      🤖 Filtering with Claude...")
            signal_data = filter_with_claude(video, channel, transcript)

            new_processed.append(vid_id)

            if not signal_data.get('relevant', False):
                print(f"      ⏭️  Not relevant — skipped")
                # Brief pause to respect API rate limits
                time.sleep(1)
                continue

            print(f"      ✅ Relevant ({signal_data.get('relevance','medium')}) — '{signal_data.get('title','')[:60]}'")

            # Generate signal markdown
            filename, content = generate_signal_md(video, channel, signal_data)

            # Create GitHub PR
            print(f"      📬 Creating PR...")
            success = create_pr(filename, content, video, channel, signal_data)
            if success:
                signals_created += 1

            time.sleep(2)  # Be polite to APIs

        print()

    # Update state with all newly seen video IDs
    state['processed_video_ids'] = list(processed_ids) + new_processed
    state['last_run'] = datetime.datetime.utcnow().isoformat() + 'Z'
    save_state(state)

    # Commit updated state file
    print(f"💾 Saving state ({len(new_processed)} new videos recorded)...")
    os.system(f'git config user.name "github-actions[bot]"')
    os.system(f'git config user.email "github-actions[bot]@users.noreply.github.com"')
    os.system(f'git add .github/yt-state.json')
    os.system(f'git diff --staged --quiet || git commit -m "chore: update YouTube tracker state [{datetime.date.today()}]"')
    os.system(f'git push origin HEAD')

    print(f"\n{'='*50}")
    print(f"✅ Done — {signals_created} signal PR(s) created")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
