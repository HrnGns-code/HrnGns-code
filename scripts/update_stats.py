# Render public GitHub metrics using only the Python standard library.
from datetime import datetime, timezone
from html import escape
import json
import os
from pathlib import Path
import re
from urllib.request import Request, urlopen

def fetch(path):
    headers = {'Accept': 'application/vnd.github+json',
               'User-Agent': 'HrnLabs-Profile', 'X-GitHub-Api-Version': '2026-03-10'}
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        headers['Authorization'] = f'Bearer {token}'
    request = Request('https://api.github.com' + path, headers=headers)
    with urlopen(request, timeout=30) as response:
        return json.load(response)

def collect(username):
    if not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?', username):
        raise ValueError('A valid GitHub username is required.')
    user = fetch('/users/' + username)
    repos = []
    page = 1
    while True:
        batch = fetch(f'/users/{username}/repos?type=owner&per_page=100&page={page}')
        repos.extend(repo for repo in batch
                     if not repo.get('private')
                     and repo['owner']['login'].lower() == username.lower())
        if len(batch) < 100:
            break
        page += 1
    originals = [repo for repo in repos if not repo['fork']]
    return [str(len(repos)), str(len(originals)),
            str(sum(repo['stargazers_count'] for repo in originals)),
            str(user['followers'])]

def render(values, subtitle):
    labels = ['PUBLIC REPOS', 'ORIGINAL REPOS', 'STARS / ORIGINALS', 'FOLLOWERS']
    cards = []
    for i, (label, value) in enumerate(zip(labels, values)):
        x = 26 + i * 292
        color = '#F06022' if i % 2 == 0 else '#9BCC4C'
        cards.append(f'''<g transform="translate({x} 80)">
<rect width="272" height="124" rx="14" fill="#16202C" stroke="#2A3949"/>
<rect x="18" y="18" width="28" height="3" rx="1" fill="{color}"/>
<text x="18" y="73" fill="{color}" font-size="42" font-weight="750">{escape(value)}</text>
<text x="18" y="104" fill="#B6C4D4" font-family="Consolas, monospace" font-size="15">{label}</text></g>''')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="265" viewBox="0 0 1200 265" role="img" aria-labelledby="title">
<title id="title">GitHub public statistics. {escape(subtitle)}</title>
<rect x="1" y="1" width="1198" height="263" rx="20" fill="#101721" stroke="#273442"/>
<g font-family="Segoe UI, Arial, sans-serif">
<text x="26" y="44" fill="#E6EDF5" font-size="23" font-weight="700">GITHUB / PUBLIC SIGNAL</text>
{''.join(cards)}
<text x="26" y="240" fill="#9DADBF" font-size="16">{escape(subtitle)}</text>
</g></svg>'''

def main():
    username = os.environ['PROFILE_USERNAME']
    values = collect(username)
    updated = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    output = Path(__file__).resolve().parents[1] / 'assets/profile-stats.svg'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(values, f'@{username} · Public data only · Updated {updated}'), encoding='utf-8')

if __name__ == '__main__':
    main()
