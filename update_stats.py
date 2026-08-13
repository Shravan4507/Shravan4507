import os
import json
import datetime
import urllib.request
import urllib.error
import base64

USER_NAME = "Shravan4507"
DEFAULT_START_DATE = datetime.datetime(2023, 1, 1)

def fetch_github_stats():
    """Fetches user stats via GitHub GraphQL API with fallback to unauthenticated/default data."""
    token = os.environ.get("ACCESS_TOKEN") or os.environ.get("PROFILE_TOKEN") or os.environ.get("GITHUB_TOKEN")
    
    stats = {
        "user": USER_NAME,
        "joined_date": DEFAULT_START_DATE,
        "repos": 15,
        "stars": 25,
        "followers": 10,
        "commits": 350,
        "contributions": 420
    }

    if not token:
        print("[INFO] No access token provided. Fetching public stats or using defaults.")
        try:
            req = urllib.request.Request(
                f"https://api.github.com/users/{USER_NAME}",
                headers={"User-Agent": "Python-Neofetch-Generator"}
            )
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                stats["repos"] = data.get("public_repos", stats["repos"])
                stats["followers"] = data.get("followers", stats["followers"])
                if data.get("created_at"):
                    stats["joined_date"] = datetime.datetime.strptime(data["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        except Exception as e:
            print(f"[WARN] Failed to fetch REST API user data: {e}")
        return stats

    headers = {
        "Authorization": f"bearer {token}",
        "User-Agent": "Python-Neofetch-Generator",
        "Content-Type": "application/json"
    }

    query = """
    query($login: String!) {
      user(login: $login) {
        createdAt
        followers { totalCount }
        repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
          totalCount
          nodes {
            stargazerCount
          }
        }
        contributionsCollection {
          totalCommitContributions
          restrictedContributionsCount
        }
      }
    }
    """

    try:
        payload = json.dumps({"query": query, "variables": {"login": USER_NAME}}).encode("utf-8")
        req = urllib.request.Request("https://api.github.com/graphql", data=payload, headers=headers)
        with urllib.request.urlopen(req) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            if "data" in res_data and res_data["data"].get("user"):
                u = res_data["data"]["user"]
                stats["followers"] = u["followers"]["totalCount"]
                stats["repos"] = u["repositories"]["totalCount"]
                stats["stars"] = sum(repo["stargazerCount"] for repo in u["repositories"]["nodes"])
                
                commits = u["contributionsCollection"]["totalCommitContributions"]
                restricted = u["contributionsCollection"]["restrictedContributionsCount"]
                stats["commits"] = commits
                stats["contributions"] = commits + restricted
                
                if u.get("createdAt"):
                    stats["joined_date"] = datetime.datetime.strptime(u["createdAt"], "%Y-%m-%dT%H:%M:%SZ")
                print("[SUCCESS] Successfully fetched live GraphQL stats!")
    except Exception as e:
        print(f"[WARN] GraphQL fetch failed ({e}). Falling back to available metrics.")

    return stats

def calculate_uptime(start_date):
    now = datetime.datetime.now()
    years = now.year - start_date.year
    months = now.month - start_date.month
    days = now.day - start_date.day

    if days < 0:
        months -= 1
        prev_month = (now.month - 1) if now.month > 1 else 12
        prev_year = now.year if now.month > 1 else now.year - 1
        import calendar
        days += calendar.monthrange(prev_year, prev_month)[1]
    if months < 0:
        years -= 1
        months += 12

    parts = []
    if years > 0:
        parts.append(f"{years} yr{'s' if years > 1 else ''}")
    if months > 0:
        parts.append(f"{months} mo{'s' if months > 1 else ''}")
    parts.append(f"{days} day{'s' if days != 1 else ''}")
    return ", ".join(parts)

def fetch_profile_image_b64(user_name):
    """Fetches user avatar (or local assets/profile.png if present) and returns base64 data URI."""
    local_img = os.path.join("assets", "profile.png")
    if os.path.exists(local_img):
        try:
            with open(local_img, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
                print("[SUCCESS] Loaded local assets/profile.png avatar!")
                return f"data:image/png;base64,{encoded}"
        except Exception as e:
            print(f"[WARN] Failed to read local profile.png: {e}")
            
    try:
        url = f"https://github.com/{user_name}.png"
        req = urllib.request.Request(url, headers={'User-Agent': 'Python-Neofetch-Generator'})
        with urllib.request.urlopen(req) as resp:
            encoded = base64.b64encode(resp.read()).decode("utf-8")
            print("[SUCCESS] Fetched & base64-encoded profile picture from GitHub!")
            return f"data:image/png;base64,{encoded}"
    except Exception as e:
        print(f"[WARN] Profile picture fetch failed: {e}")
        return None

def generate_neofetch_svg(stats, theme="dark", profile_b64=None):
    is_dark = (theme == "dark")
    
    # Palette definition
    bg_color = "#0b0e14" if is_dark else "#ffffff"
    border_color = "#1f293d" if is_dark else "#e2e8f0"
    header_bar = "#131924" if is_dark else "#f1f5f9"
    title_color = "#89b4fa" if is_dark else "#2563eb"
    prompt_color = "#a6e3a1" if is_dark else "#059669"
    key_color = "#89b4fa" if is_dark else "#2563eb"
    val_color = "#cdd6f4" if is_dark else "#0f172a"
    accent_color = "#f38ba8" if is_dark else "#dc2626"
    sub_color = "#9399b2" if is_dark else "#64748b"
    glow_border = "#89b4fa" if is_dark else "#3b82f6"

    uptime_str = calculate_uptime(stats["joined_date"])

    info_lines = [
        ("OS", "Agentic AI OS v4.0 (x86_64)"),
        ("Uptime", uptime_str),
        ("Host", "Model Context Protocol (MCP)"),
        ("Repos", f"{stats['repos']} public repositories"),
        ("Commits", f"{stats['commits']} total contributions"),
        ("Stars", f"{stats['stars']} stars earned"),
        ("Followers", f"{stats['followers']} network nodes"),
        ("Stack", "React • TypeScript • Python • MCP"),
        ("Status", "Everything is RELATIVE..."),
    ]

    # Render SVG XML
    svg_lines = []
    svg_lines.append(f'<svg width="780" height="340" viewBox="0 0 780 340" fill="none" xmlns="http://www.w3.org/2000/svg">')
    svg_lines.append(f'  <defs>')
    svg_lines.append(f'    <clipPath id="avatar-clip">')
    svg_lines.append(f'      <rect x="35" y="60" width="145" height="145" rx="18" />')
    svg_lines.append(f'    </clipPath>')
    svg_lines.append(f'  </defs>')
    svg_lines.append(f'  <style>')
    svg_lines.append(f'    .bg {{ fill: {bg_color}; stroke: {border_color}; stroke-width: 1.5; rx: 16px; }}')
    svg_lines.append(f'    .header-bar {{ fill: {header_bar}; rx: 16px; }}')
    svg_lines.append(f'    .title {{ fill: {title_color}; font-family: "Fira Code", "Cascadia Code", "JetBrains Mono", "Courier New", monospace; font-size: 15px; font-weight: 700; }}')
    svg_lines.append(f'    .user {{ fill: {prompt_color}; font-weight: 700; }}')
    svg_lines.append(f'    .sep {{ fill: {sub_color}; }}')
    svg_lines.append(f'    .key {{ fill: {key_color}; font-family: "Fira Code", "Cascadia Code", "JetBrains Mono", "Courier New", monospace; font-size: 13px; font-weight: 600; }}')
    svg_lines.append(f'    .val {{ fill: {val_color}; font-family: "Fira Code", "Cascadia Code", "JetBrains Mono", "Courier New", monospace; font-size: 13px; }}')
    svg_lines.append(f'    .badge-txt {{ fill: {val_color}; font-family: "Fira Code", "Cascadia Code", monospace; font-size: 12px; font-weight: 700; }}')
    svg_lines.append(f'  </style>')

    # Background window
    svg_lines.append(f'  <rect x="1" y="1" width="778" height="338" class="bg" />')
    
    # Top terminal bar
    svg_lines.append(f'  <path d="M1 17C1 8.16344 8.16344 1 17 1H763C771.837 1 779 8.16344 779 17V36H1V17Z" class="header-bar" />')
    svg_lines.append(f'  <circle cx="20" cy="18" r="5.5" fill="#ff5f56" />')
    svg_lines.append(f'  <circle cx="36" cy="18" r="5.5" fill="#ffbd2e" />')
    svg_lines.append(f'  <circle cx="52" cy="18" r="5.5" fill="#27c93f" />')
    svg_lines.append(f'  <text x="390" y="23" text-anchor="middle" class="val" font-size="12" fill="{sub_color}">shravan@antigravity-core:~</text>')

    # Avatar Image (Left Side)
    if profile_b64:
        svg_lines.append(f'  <image href="{profile_b64}" x="35" y="60" width="145" height="145" clip-path="url(#avatar-clip)" />')
        svg_lines.append(f'  <rect x="35" y="60" width="145" height="145" rx="18" fill="none" stroke="{glow_border}" stroke-width="2" />')
    else:
        # Fallback rect
        svg_lines.append(f'  <rect x="35" y="60" width="145" height="145" rx="18" fill="{header_bar}" stroke="{glow_border}" stroke-width="2" />')

    # Profile Badges under Avatar
    svg_lines.append(f'  <rect x="35" y="220" width="145" height="28" rx="8" fill="{header_bar}" stroke="{border_color}" />')
    svg_lines.append(f'  <text x="107" y="238" text-anchor="middle" class="badge-txt" fill="{prompt_color}">SHRVAN // OS</text>')

    svg_lines.append(f'  <rect x="35" y="258" width="145" height="26" rx="8" fill="{header_bar}" stroke="{border_color}" />')
    svg_lines.append(f'  <text x="107" y="275" text-anchor="middle" class="val" font-size="11" fill="{sub_color}">Agentic AI Core</text>')

    # Vertical Separator Line
    svg_lines.append(f'  <line x1="215" y1="50" x2="215" y2="310" stroke="{border_color}" stroke-width="1.5" stroke-dasharray="4 4" />')

    # Right Side Content Header
    svg_lines.append(f'  <text x="240" y="70" class="title"><tspan class="user">shravan</tspan>@<tspan fill="{val_color}">antigravity-core</tspan></text>')
    svg_lines.append(f'  <text x="240" y="85" class="sep">-----------------------------------------</text>')

    # System Info Key-Values
    y_info = 110
    for key, val in info_lines:
        svg_lines.append(f'  <text x="240" y="{y_info}" class="key">{key}: <tspan class="val">{val}</tspan></text>')
        y_info += 21

    # Terminal Color Blocks Palette (Bottom Right)
    colors = ["#f38ba8", "#fab387", "#f9e2af", "#a6e3a1", "#89b4fa", "#cba6f7", "#f5e0dc", "#585b70"]
    x_color = 240
    for c in colors:
        svg_lines.append(f'  <rect x="{x_color}" y="300" width="22" height="14" rx="3" fill="{c}" />')
        x_color += 28

    svg_lines.append(f'</svg>')
    return "\n".join(svg_lines)

def main():
    print("[INIT] Fetching GitHub Stats for Neofetch banner...")
    stats = fetch_github_stats()
    profile_b64 = fetch_profile_image_b64(USER_NAME)
    
    os.makedirs("assets", exist_ok=True)

    dark_svg = generate_neofetch_svg(stats, theme="dark", profile_b64=profile_b64)
    dark_path = os.path.join("assets", "neofetch_dark.svg")
    with open(dark_path, "w", encoding="utf-8") as f:
        f.write(dark_svg)
    print(f"[DONE] Saved Dark Neofetch SVG -> {dark_path}")

    light_svg = generate_neofetch_svg(stats, theme="light", profile_b64=profile_b64)
    light_path = os.path.join("assets", "neofetch_light.svg")
    with open(light_path, "w", encoding="utf-8") as f:
        f.write(light_svg)
    print(f"[DONE] Saved Light Neofetch SVG -> {light_path}")

if __name__ == "__main__":
    main()

