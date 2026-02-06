import re
import argparse
import sys
import os

def parse_report(filepath):
    """Parses the text report into a structured list of groups."""
    groups = []
    current_group = None
    
    # Regex patterns
    group_header_re = re.compile(r"Group (\d+): (.+)")
    score_re = re.compile(r"Total Group Satisfaction Score: (.+)")
    member_re = re.compile(r"\s+-\s+(.+) \((.+)\)")
    raw_score_re = re.compile(r"\s+Raw Score Contribution: (\d+)")
    details_re = re.compile(r"\s+Details: (.+)")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    for line in lines:
        line = line.strip('\n') # Keep leading spaces for indent detection
        
        # Group Header
        m = group_header_re.match(line)
        if m:
            if current_group:
                groups.append(current_group)
            current_group = {
                "id": m.group(1),
                "subject": m.group(2).strip(),
                "score": 0,
                "members": []
            }
            continue
            
        # Total Score
        m = score_re.match(line.strip())
        if m and current_group:
            current_group["score"] = m.group(1).strip()
            continue
            
        # Member Name
        # Check for member line (indented)
        if line.strip().startswith("-") and current_group:
            m = member_re.match(line)
            if m:
                current_group["members"].append({
                    "name": m.group(1).strip(),
                    "email": m.group(2).strip(),
                    "raw_score": 0,
                    "details": ""
                })
            continue

        # Member Stats
        if current_group and current_group["members"]:
            last_member = current_group["members"][-1]
            
            m = raw_score_re.match(line)
            if m:
                last_member["raw_score"] = m.group(1)
                continue
                
            m = details_re.match(line)
            if m:
                last_member["details"] = m.group(1)
                continue

    if current_group:
        groups.append(current_group)
        
    return groups

def generate_html(groups, output_file):
    """Generates a modern HTML infographic."""
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Group Attribution Results</title>
    <style>
        :root {{
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent-color: #38bdf8;
            --border-color: #334155;
        }}
        
        body {{
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            margin: 0;
            padding: 40px 20px;
            line-height: 1.5;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        header {{
            text-align: center;
            margin-bottom: 60px;
        }}
        
        h1 {{
            font-size: 2.5rem;
            font-weight: 800;
            margin: 0;
            background: linear-gradient(to right, #38bdf8, #818cf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .subtitle {{
            color: var(--text-secondary);
            font-size: 1.1rem;
            margin-top: 10px;
        }}

        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 24px;
        }}
        
        .card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            overflow: hidden;
            transition: transform 0.2s, box-shadow 0.2s;
            position: relative;
        }}
        
        .card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 10px 30px -10px rgba(0,0,0,0.5);
            border-color: var(--accent-color);
        }}
        
        .card-header {{
            padding: 24px;
            border-bottom: 1px solid var(--border-color);
            background: linear-gradient(to bottom right, rgba(255,255,255,0.03), transparent);
            position: relative;
        }}
        
        .group-id {{
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.1em;
            color: var(--text-secondary);
            font-weight: 600;
            margin-bottom: 8px;
        }}
        
        .subject-title {{
            font-size: 1.25rem;
            font-weight: 700;
            color: #fff;
            margin: 0;
            padding-right: 60px; /* Space for score */
        }}
        
        .total-score {{
            position: absolute;
            top: 24px;
            right: 24px;
            background: rgba(56, 189, 248, 0.1);
            color: var(--accent-color);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.875rem;
            font-weight: 600;
            border: 1px solid rgba(56, 189, 248, 0.2);
        }}
        
        .members-list {{
            padding: 24px;
        }}
        
        .member {{
            display: flex;
            align-items: flex-start;
            margin-bottom: 20px;
            padding-bottom: 20px;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }}
        
        .member:last-child {{
            border-bottom: none;
            margin-bottom: 0;
            padding-bottom: 0;
        }}
        
        .avatar {{
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: linear-gradient(135deg, #6366f1, #a855f7);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            margin-right: 16px;
            flex-shrink: 0;
            font-size: 1rem;
        }}
        
        .member-info {{
            flex: 1;
        }}
        
        .member-name {{
            font-weight: 600;
            font-size: 1rem;
            color: #e2e8f0;
            margin-bottom: 2px;
        }}
        
        .member-email {{
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin-bottom: 8px;
        }}

        .member-score {
            font-size: 0.75rem;
            color: #fff;
            background: linear-gradient(135deg, #10b981, #059669);
            font-weight: 700;
            margin-left: 10px;
            padding: 2px 8px;
            border-radius: 6px;
            display: inline-block;
            vertical-align: middle;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        
        .badges {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }}
        
        .badge {{
            font-size: 0.7rem;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 6px;
            display: inline-flex;
            align-items: center;
        }}
        
        /* 1st Choice (+100) */
        .badge-green {{
            background: rgba(74, 222, 128, 0.15);
            color: #4ade80;
            border: 1px solid rgba(74, 222, 128, 0.2);
        }}
        /* 2nd Choice (+80) */
        .badge-lime {{
            background: rgba(163, 230, 53, 0.15);
            color: #a3e635;
            border: 1px solid rgba(163, 230, 53, 0.2);
        }}
        /* 3rd Choice (+60) */
        .badge-yellow {{
            background: rgba(250, 204, 21, 0.15);
            color: #facc15;
            border: 1px solid rgba(250, 204, 21, 0.2);
        }}
        /* 4th Choice (+40) */
        .badge-orange {{
            background: rgba(251, 146, 60, 0.15);
            color: #fb923c;
            border: 1px solid rgba(251, 146, 60, 0.2);
        }}
        /* 5th Choice (+20) */
        .badge-red {{
            background: rgba(248, 113, 113, 0.15);
            color: #f87171;
            border: 1px solid rgba(248, 113, 113, 0.2);
        }}
        /* Unranked (0) */
        .badge-gray {{
            background: rgba(148, 163, 184, 0.15);
            color: #94a3b8;
            border: 1px solid rgba(148, 163, 184, 0.2);
        }}
        /* Partner Match (+25) */
        .badge-blue {{
            background: rgba(56, 189, 248, 0.15);
            color: #38bdf8;
            border: 1px solid rgba(56, 189, 248, 0.2);
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Attribution Results</h1>
            <div class="subtitle">Generated from Solver Report • {len(groups)} Groups Formed</div>
        </header>
        
        <div class="grid">
    """
    
    # Regex helper to parse details string
    # "Subject Rank 1 (+100), Partner Match: jihad.ouard@imt-atlantique.net (Raw +25)"
    subject_rank_re = re.compile(r"Subject Rank (\d+) \(\+(\d+)\)")
    subject_unranked_re = re.compile(r"Subject Unranked")
    partner_re = re.compile(r"Partner Match: ([^ ]+) \(Raw \+(\d+)\)")
    
    for g in groups:
        html_content += f"""
            <div class="card">
                <div class="card-header">
                    <div class="group-id">Group {g['id']}</div>
                    <h2 class="subject-title">{g['subject']}</h2>
                    <div class="total-score">{g['score']} pts</div>
                </div>
                <div class="members-list">
        """
        
        for m in g['members']:
            initials = "".join([n[0] for n in m['name'].split()[:2]])
            details = m['details']
            
            badges_html = ""
            
            # 1. Subject Badge
            sub_m = subject_rank_re.search(details)
            if sub_m:
                rank = int(sub_m.group(1))
                score = int(sub_m.group(2))
                
                badge_class = "badge-gray"
                if score == 100: badge_class = "badge-green"
                elif score == 80: badge_class = "badge-lime"
                elif score == 60: badge_class = "badge-yellow"
                elif score == 40: badge_class = "badge-orange"
                elif score == 20: badge_class = "badge-red"
                
                badges_html += f'<span class="badge {badge_class}">Subject Rank {rank} (+{score})</span>'
            elif subject_unranked_re.search(details):
                badges_html += '<span class="badge badge-gray">Unranked (+0)</span>'
                
            # 2. Partner Badges
            # Find all partner matches
            for p_m in partner_re.finditer(details):
                partner_email = p_m.group(1)
                # Keep email short? nah, just show "Partner Match" or +25
                # User asked for blue badge
                badges_html += f'<span class="badge badge-blue">Partner Match (+25)</span>'
            
            # Self-choice warning?
            if "Ignored self-choice" in details:
                 badges_html += f'<span class="badge badge-gray">Self-choice Ignored</span>'

            html_content += f"""
                    <div class="member">
                        <div class="avatar">{initials}</div>
                        <div class="member-info">
                            <div class="member-name">
                                {m['name']}
                                <span class="member-score">+{m['raw_score']}</span>
                            </div>
                            <div class="member-email">{m['email']}</div>
                            <div class="badges">
                                {badges_html}
                            </div>
                        </div>
                    </div>
            """
            
        html_content += """
                </div>
            </div>
        """
        
    html_content += """
        </div>
    </div>
</body>
</html>
    """
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print(f"Successfully generated {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Visualize Attribution Report")
    parser.add_argument("input_report", help="Path to the .txt report file")
    parser.add_argument("output_html", help="Path to the output .html file")
    args = parser.parse_args()
    
    if not os.path.exists(args.input_report):
        print(f"Error: File {args.input_report} not found.")
        sys.exit(1)
        
    groups = parse_report(args.input_report)
    generate_html(groups, args.output_html)

if __name__ == "__main__":
    main()
