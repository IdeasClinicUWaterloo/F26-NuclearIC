# Security

## Overview

Small Modular Reactors (SMRs) require robust security systems to protect facilities and prevent unauthorized access. In this challenge, you'll design a **Physical Protection System (PPS)** for a fictional SMR facility, drawing from real nuclear security principles used by the NRC and IAEA.

Your goal is to balance security with operational efficiency. You'll need to think critically about who needs access where, under what conditions, and how to handle emergencies.

## What You'll Do

### 1. Review the Facility

You'll receive:
- A **facility map** showing security zones (reactor building, control room, maintenance areas, administrative offices, perimeter, etc.)
- **Personnel role descriptions** (reactor operator, security officer, maintenance technician, contractor, visitor, emergency responder)
- A brief introduction to **defense-in-depth** security and access control concepts

### 2. Design Your Access Control Policy

Using a digital interface, you'll:
- Assign access levels for each personnel role to each security zone (e.g., "Permitted", "Restricted", "Denied")
- Add conditions to your access rules, such as:
  - Time-of-day restrictions (e.g., "only during business hours")
  - Escort requirements (e.g., "contractors must have a security officer present")
  - Zone dependencies (e.g., "you must have cleared Zone 2 before accessing Zone 3")
- Define how your access rules change during an emergency/alert state (e.g., fast-path protocols for critical personnel, lockdowns for sensitive areas)
- Justify your decisions based on security principles

### 3. Answer Edge Case Scenarios

During the challenge, you'll be presented with real-world scenarios that test your policy logic. Examples:
- An access card is lost at 2am
- An emergency is declared and an on-call operator is currently in an administrative area
- A contractor's escort unexpectedly leaves a restricted area

You'll answer based on your own policy rule. There's no right answer, but your response must be consistent with what you designed.

### 4. Test Against Bad Actors

After submitting your policy, the system will automatically test it against different attacker patterns that can commonly be encountered in real world security scenarios.

### 5. Revise and Resubmit

Based on your results, you can revise your policy and resubmit for re-evaluation. Iteration is a critical part of real-world security design.

## How You'll Be Judged

Your submission will be evaluated on:

- **Policy Completeness**: Does your policy cover all personnel roles and zones? Are alert-state rules defined?
- **Security Effectiveness**: How many bad actors did you stop? Where did the ones that got through exploit gaps?
- **Scenario Responses**: Are your edge case answers consistent with your policy? Do they make sense operationally?
- **Justified Reasoning**: Can you explain *why* you made each major decision?
- **Feasibility**: Does your policy balance security with realistic facility operations?

## Key Concepts

Some concepts you can consider when design zones and policies:

**Defense-in-Depth:** Multiple layers of security so a single breach doesn't compromise the entire facility.

**Least Privilege:** Users get the minimum access required to do their job, nothing more.

**Zone Gradient:** Security increases as you move toward more critical areas; higher-security areas have stricter entry requirements.

**Two-Person Rule:** Critical decisions or access require authorization from two independent people.

**Emergency/Alert Protocols:** Clear rules for how access changes during security events—typically some fast-paths for essential personnel, lockdowns for sensitive areas.
