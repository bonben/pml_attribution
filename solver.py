from ortools.sat.python import cp_model

def solve_attribution(students, subjects, target_group_size=3):
    """
    students: list of dicts {
        'id': str/int, 
        'partner_choices': [id1, id2], 
        'subject_ranks': [sub_id1, sub_id2, sub_id3] 
    }
    subjects: list of dicts {'id': str/int, 'name': str}
    """
    
    if not students or not subjects:
        return None

    num_students = len(students)
    # Heuristic: Target group size 3
    num_groups = (num_students + target_group_size - 1) // target_group_size 

    model = cp_model.CpModel()

    # Variables
    # x[s_idx, g] = 1 if student s is in group g
    x = {}
    for s_idx, s in enumerate(students):
        for g in range(num_groups):
            x[s_idx, g] = model.NewBoolVar(f'x_s{s["id"]}_g{g}')
            
    # y[g, sub_idx] = 1 if group g is assigned subject sub
    y = {}
    for g in range(num_groups):
        for sub_idx, sub in enumerate(subjects):
            y[g, sub_idx] = model.NewBoolVar(f'y_g{g}_sub{sub["id"]}')

    # Constraints
    
    # 1. Each student in exactly one group
    for s_idx in range(num_students):
        model.Add(sum(x[s_idx, g] for g in range(num_groups)) == 1)

    # 2. Group size constraints
    # Min 2, max 3. Target 3.
    # User Requirement: Never 4. 2 groups of 2 is better than 1 of 4.
    for g in range(num_groups):
        size = sum(x[s_idx, g] for s_idx in range(num_students))
        model.Add(size >= 2)
        model.Add(size <= 3)
        
        # Each group must have exactly one subject
        model.Add(sum(y[g, sub_idx] for sub_idx in range(len(subjects))) == 1)

    # 3. Subject Uniqueness: A subject must not be assigned twice
    for sub_idx in range(len(subjects)):
        model.Add(sum(y[g, sub_idx] for g in range(num_groups)) <= 1)

    # Objective Function
    obj_terms = [] # All objective terms will be added here

    # Map student ID to index for easier lookup
    id_to_idx = {s['id']: i for i, s in enumerate(students)}
    
    # 1. Partner Preferences
    # Per-group partner score accumulation
    group_partner_scores = [[] for _ in range(num_groups)]

    for s_idx in range(num_students):
        s = students[s_idx]
        
        for choice_priority, partner_id in enumerate(s.get('partner_choices', [])):
            if partner_id in id_to_idx:
                p_idx = id_to_idx[partner_id]
                weight = 25 # Compromise: High enough to keep mutuals together (25+25 > 20+20 drop)
                
                for g in range(num_groups):
                    b_together = model.NewBoolVar(f'together_{s_idx}_{p_idx}_{g}')
                    # b_together is true ONLY if both s and p are in group g
                    model.AddBoolAnd([x[s_idx, g], x[p_idx, g]]).OnlyEnforceIf(b_together)
                    model.AddBoolOr([x[s_idx, g].Not(), x[p_idx, g].Not()]).OnlyEnforceIf(b_together.Not())
                    
                    # Add to group list
                    group_partner_scores[g].append(b_together * weight)

    # Apply CAP per group
    # Cap = 80. 
    # Logic: capped_score <= raw_sum AND capped_score <= 80. 
    # Since we Maximize, it will push to min(raw, 80).
    for g in range(num_groups):
        if group_partner_scores[g]:
            raw_sum = sum(group_partner_scores[g])
            # Removed CAP: capped_var logic removed
            obj_terms.append(raw_sum)

    # 2. Subject Preferences
    # Map subject ID to index
    sub_id_to_idx = {sub['id']: i for i, sub in enumerate(subjects)}
    
    for s_idx, s in enumerate(students):
        # s['subject_ranks'] is a list of subject IDs in order of preference
        ranks = {sub_id: rank for rank, sub_id in enumerate(s.get('subject_ranks', []))}
        
        for g in range(num_groups):
            for sub_idx, sub in enumerate(subjects):
                # Calculate cost/reward
                # Rank 0 (1st choice) -> Reward 20
                # Rank 1 (2nd choice) -> Reward 15
                # Rank 2 (3rd choice) -> Reward 10
                # Unranked -> Reward 0
                
                rank = ranks.get(sub['id'])
                reward = 0
                if rank == 0: reward = 100
                elif rank == 1: reward = 80
                elif rank == 2: reward = 60
                elif rank == 3: reward = 40   # 4th Choice
                elif rank == 4: reward = 20   # 5th Choice
                
                if reward > 0:
                    z = model.NewBoolVar(f'z_{s_idx}_{g}_{sub_idx}')
                    model.AddBoolAnd([x[s_idx, g], y[g, sub_idx]]).OnlyEnforceIf(z)
                    model.AddBoolOr([x[s_idx, g].Not(), y[g, sub_idx].Not()]).OnlyEnforceIf(z.Not())
                    obj_terms.append(reward * z)

    # 3. Target Group Size 3
    for g in range(num_groups):
        is_3 = model.NewBoolVar(f'g{g}_is_3')
        model.Add(sum(x[s_idx, g] for s_idx in range(num_students)) == 3).OnlyEnforceIf(is_3)
        obj_terms.append(50 * is_3)

    # Solve
    model.Maximize(sum(obj_terms))
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    results = []
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for g in range(num_groups):
            group_members = []
            for s_idx in range(num_students):
                if solver.Value(x[s_idx, g]):
                    group_members.append(students[s_idx])
            
            if not group_members: continue
            
            assigned_subject = None
            for sub_idx, sub in enumerate(subjects):
                if solver.Value(y[g, sub_idx]):
                    assigned_subject = sub
                    break
            
            # Calculate Score Details for Report
            member_details = []
            group_subject_score = 0
            group_partner_raw_score = 0
            
            # Map IDs for easy lookup
            member_ids = {m['id'] for m in group_members}
            
            # 1. Calculate Subject Scores
            for s in group_members:
                sub_score = 0
                notes = []
                # ... Subject Logic ...
                rank = -1
                if assigned_subject:
                    try:
                        rank = s['subject_ranks'].index(assigned_subject['id'])
                        if rank == 0: sub_score = 100
                        elif rank == 1: sub_score = 80
                        elif rank == 2: sub_score = 60
                        elif rank == 3: sub_score = 40
                        elif rank == 4: sub_score = 20
                        
                        notes.append(f"Subject Rank {rank+1} (+{sub_score})")
                    except ValueError:
                        notes.append("Subject Unranked (+0)")
                
                # Partner Raw Calculation (per student contribution)
                p_contribution = 0
                for idx, partner_id in enumerate(s.get('partner_choices', [])):
                    if partner_id in member_ids:
                        p_contribution += 25
                        notes.append(f"Partner Match: {partner_id} (Raw +25)")
                
                if s.get('warnings'):
                    notes.extend(s['warnings'])
                
                group_subject_score += sub_score
                group_partner_raw_score += p_contribution
                
                member_details.append({
                    "name": s['name'],
                    "email": s['email'],
                    "raw_score": sub_score + p_contribution, # For CSV roughly
                    "notes": ", ".join(notes)
                })

            # Apply Partner Cap: REMOVED
            capped_partner_score = group_partner_raw_score
            total_group_score = group_subject_score + capped_partner_score
            
            # Add a meta-detail for the report regarding the cap
            cap_note = ""

            results.append({
                "group_id": g + 1,
                "members": group_members,
                "subject": assigned_subject,
                "details": member_details,
                "total_score": f"{total_group_score} {cap_note}"
            })
        return results
    else:
        return None
