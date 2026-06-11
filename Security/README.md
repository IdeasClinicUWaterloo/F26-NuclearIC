# Security

## Overview

Small Modular Reactors (SMRs) require robust security systems to protect facilities and prevent unauthorized access. In this challenge, you'll design a **Physical Protection System (PPS)** for a fictional SMR facility, drawing from real nuclear security principles used by the NRC and IAEA.

Your goal is to balance security with operational efficiency. You'll need to think critically about who needs access where, under what conditions, and how to handle emergencies.

## What You'll Do

### 1. Review the Facility

You'll receive:
- A facility map showing security zones (reactor building, control room, maintenance areas, administrative offices, perimeter, etc.)
- Personnel role descriptions (reactor operator, security officer, maintenance technician, contractor, visitor, emergency responder)
- A brief introduction to **defense-in-depth** security and access control concepts

### 2. Design Your Access Control Policy

You will:
- Assign access levels for each personnel role to each security zone (e.g., "Permitted", "Restricted", "Denied")
- Add conditions to your access rules
- Define how your access rules change during an emergency/alert state
- Justify your decisions based on security principles

### 3. Answer Edge Case Scenarios

During the challenge, you'll be presented with real-world scenarios that test your policy logic. You'll answer based on your own policy rule. There's no right answer, but your response must be consistent with what you designed.

### 4. Test Against Bad Actors

After submitting your policy, the system will automatically test it against different attacker patterns that can commonly be encountered in real world security scenarios.

### 5. Revise and Resubmit

Based on your results, you can revise your policy and resubmit for re-evaluation. Iteration is a critical part of real-world security design.

## How You'll Be Judged

Your submission will be evaluated on:

- **Security Effectiveness**: How many bad actors did you stop? Did you consider multiple scenarios of attack?
- **Scenario Responses**: Are your edge case answers consistent with your policy? Do they make sense operationally?
- **Feasibility**: Does your policy balance security with realistic facility operations?
