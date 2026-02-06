import csv
import argparse
import sys
from solver import solve_attribution

def main():
    parser = argparse.ArgumentParser(description="Student Group Attribution from CSV")
    parser.add_argument("--input", required=True, help="Input CSV file path")
    parser.add_argument("--output", required=True, help="Output CSV file path")
    args = parser.parse_args()

    students = []
    # Set of all unique subjects encountered
    all_subject_names = set()

    print(f"Reading input from {args.input}...")
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            # Normalize headers: strip whitespace
            reader.fieldnames = [name.strip() for name in reader.fieldnames]
            
            # Identify Subject Columns
            # Format: "Rank your Top 5 Subject Preferences ... [Subject Name]"
            subject_map = {} # "Header Name" -> "Subject Name"
            for header in reader.fieldnames:
                if "Rank your Top 5 Subject Preferences" in header and "[" in header and "]" in header:
                    # Extract content between brackets
                    start = header.rfind("[") + 1
                    end = header.rfind("]")
                    if start > 0 and end > start:
                        subject_name = header[start:end].strip()
                        subject_map[header] = subject_name
                        all_subject_names.add(subject_name)

            for row in reader:
                email = row.get('Your email', '').strip()
                if not email:
                    continue

                s_dict = {
                    'id': email,
                    'name': email.split('@')[0].replace('.', ' ').title(), # Fallback name extraction
                    'email': email,
                    'partner_choices': [],
                    'subject_ranks': [] # list of subject names in order
                }
                
                # Partners: "Student 1", "Student 2"
                s_dict['warnings'] = []
                
                p1 = row.get('Student 1', '').strip()
                if p1: 
                    if p1 == email:
                        s_dict['warnings'].append(f"Ignored self-choice (Student 1)")
                    elif p1 not in s_dict['partner_choices']:
                        s_dict['partner_choices'].append(p1)
                
                p2 = row.get('Student 2', '').strip()
                if p2: 
                    if p2 == email:
                        s_dict['warnings'].append(f"Ignored self-choice (Student 2)")
                    elif p2 not in s_dict['partner_choices']:
                        s_dict['partner_choices'].append(p2)
                    
                # Parse Subject Ranks
                # Values are "1st Choice", "2nd Choice", etc.
                # key = rank_int, value = subject_name
                temp_ranks = {} 
                
                for header, subject_name in subject_map.items():
                    val = row.get(header, '').strip().lower()
                    if "1st" in val: temp_ranks[0] = subject_name
                    elif "2nd" in val: temp_ranks[1] = subject_name
                    elif "3rd" in val: temp_ranks[2] = subject_name
                    elif "4th" in val: temp_ranks[3] = subject_name
                    elif "5th" in val: temp_ranks[4] = subject_name
                
                # Sort by rank and add to subject_ranks
                for r in sorted(temp_ranks.keys()):
                    s_dict['subject_ranks'].append(temp_ranks[r])
                
                students.append(s_dict)
                
    except FileNotFoundError:
        print(f"Error: Input file {args.input} not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        sys.exit(1)

    subjects = [{'id': name, 'name': name} for name in all_subject_names]
    
    print(f"Found {len(students)} students and {len(subjects)} unique subjects.")
    print("Running solver...")
    
    results = solve_attribution(students, subjects)
    
    if not results:
        print("No feasible solution found.")
        sys.exit(1)
        
    
    print(f"Success! Formed {len(results)} groups.")
    
    # Generate Detailed Report
    if args.output.endswith(".csv"):
        report_filename = args.output.replace(".csv", "_report.txt")
    else:
        report_filename = args.output + "_report.txt"
    print(f"Writing detailed report to {report_filename}...")
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write("Student Attribution Detailed Report\n")
        f.write("===================================\n\n")
        
        for group in results:
            sub_name = group['subject']['name'] if group['subject'] else "Unassigned"
            f.write(f"Group {group['group_id']}: {sub_name}\n")
            f.write(f"Total Group Satisfaction Score: {group['total_score']}\n")
            f.write("-" * 40 + "\n")
            
            for m in group['details']:
                f.write(f"  - {m['name']} ({m['email']})\n")
                f.write(f"    Raw Score Contribution: {m['raw_score']}\n")
                f.write(f"    Details: {m['notes']}\n")
            f.write("\n")

    print(f"Writing CSV results to {args.output}...")
    with open(args.output, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Group ID", "Subject", "Student Name", "Student Email", "Individual Score", "Notes"])
        
        for group in results:
            g_id = group['group_id']
            sub_name = group['subject']['name'] if group['subject'] else "Unassigned"
            
            for m in group['details']:
                writer.writerow([g_id, sub_name, m['name'], m['email'], m['raw_score'], m['notes']])
                
    print("Done.")

if __name__ == "__main__":
    main()
