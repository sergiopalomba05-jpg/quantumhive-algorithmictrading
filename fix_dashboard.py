import re

with open(r'C:\Users\sergio\QUANTUMHIVE_ALGORITHMICTRADING\dashboard\quantumhive_dashboard_v2.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

balance = 0
issues = []
for i, line in enumerate(lines, 1):
    opens = len(re.findall(r'<div\b', line, re.IGNORECASE))
    closes = len(re.findall(r'</div>', line, re.IGNORECASE))
    balance += opens - closes
    if balance < 0:
        issues.append((i, balance, line.strip()[:80]))

print(f'Total lines: {len(lines)}')
print(f'Final balance: {balance}')
print(f'Negative points: {len(issues)}')
for issue in issues[:10]:
    print(f'  Line {issue[0]}: balance={issue[1]} | {issue[2]}')

# Find line numbers of panel starts
panels = []
for i, line in enumerate(lines, 1):
    if re.search(r'<div\b[^>]*class=["\']panel', line, re.I):
        panels.append((i, 'OPEN panel', line.strip()[:80]))
    if re.search(r'<!--\s*={10,}\s*PANEL', line, re.I):
        panels.append((i, 'COMMENT', line.strip()[:80]))

print('\nPanels/comments:')
for p in panels:
    print(f'  {p[0]:4d}: {p[1]} | {p[2]}')
