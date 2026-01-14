# How Groups and Subjects are Assigned

To ensure fairness, the group formation and subject attribution process is performed by an optimization algorithm (Constraint Satisfaction Solver). This avoids manual bias and maximizes the overall satisfaction of the entire class.

Here is exactly how the algorithm works:

## 1. Goal
The system tries to maximize a global "Satisfaction Score". It tests millions of combinations to find the one that gives the highest total score for everyone.

## 2. Priorities
The score is calculated based on three main criteria, in this order of importance:

### A. Group Size (Highest Priority)
- The algorithm aims for groups of **3 students**.
- Groups of 2 or 4 are allowed only if mathematically necessary (e.g., if the total number of students isn't divisible by 3).

### B. Partner Preferences
We want you to be with people you chose. 
- **1st Choice Partner**: If you are placed in a group with your 1st choice, the system gets a large point boost (+10 points).
- **2nd Choice Partner**: If you are placed with your 2nd choice, it gets a smaller boost (+5 points).
- **Mutual Choices**: If you pick someone AND they pick you back, the points stack up, making it extremely likely you will be grouped together.

### C. Subject Preferences
We want your group to work on a topic you like.
- **1st Choice Subject**: +20 points.
- **2nd Choice Subject**: +15 points.
- **3rd Choice Subject**: +10 points.
- **4th/5th... Choice**: +0 points.

*Note: The system considers the preferences of ALL group members. It will try to find a subject that is highly ranked by everyone in the group, rather than giving one person their top choice and others their last choice.*

## Summary
The algorithm looks for a solution that:
1.  Keeps group sizes correct (3 ideal).
2.  Maximizes the number of students paired with their preferred partners.
3.  Assigns subjects that the group members collectively ranked highest.

It is a mathematical guarantee that the result is the "best possible compromise" given everyone's constraints.

## 3. Technical Details (For the Curious)
The problem is modeled as a **Constraint Satisfaction Problem (CP)** and solved using Google's **OR-Tools (CP-SAT Solver)**.

### The Algorithm: CP-SAT
The problem is modeled as a **Constraint Satisfaction Problem (CP)** and solved using Google's **OR-Tools (CP-SAT Solver)**.

Unlike "heuristic" algorithms (like Genetic Algorithms or Simulated Annealing) which guess and improve, this approach is **exact and exhaustive**.

#### How it explores the solution space
The solver doesn't just randomly flip switches. It uses advanced mathematical techniques to navigate the billions of possible combinations efficiently:

1.  **Propagation (Deduction)**: 
    The solver looks at your constraints and "deduces" forced moves. 
    *Example: "If Alice is in Group 1, and Group 1 is full, then Bob cannot be in Group 1."*
    It cascades these logical deductions instantly, pruning massive chunks of the "search tree" that are impossible.

2.  **Branching and Backtracking**:
    When logic alone isn't enough, it makes a tentative decision (e.g., "Let's try putting Charlie in Group 2"). It then propagates the consequences.
    - If it hits a contradiction (e.g., "Oops, now Group 2 has 5 people"), it **backtracks** immediately, undoing that decision and marking it as invalid.
    - This intelligent trial-and-error allows it to explore the entire feasible mathematical space without checking every single option one by one.

#### Global Optimality
Because of this structured search, when the solver finishes and says "Optimal", it has **mathematically proven** that no better solution exists. It has implicitly checked or logically ruled out every other possibility.
