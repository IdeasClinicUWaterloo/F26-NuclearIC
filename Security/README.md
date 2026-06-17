# Security

## Overview

Small Modular Reactors (SMRs) represent the next generation of nuclear energy, featuring compact designs, factory fabrication, and passive safety systems. However, their smaller physical footprints and potential deployment in remote or distributed locations introduce unique security challenges. A robust **Physical Protection System (PPS)** must safeguard the facility against radiological sabotage and the theft of sensitive materials while remaining operationally viable.

In this challenge, you will act as a member of the Systems Security Team. Your objective is to design an access control policy and zone topography for a fictional SMR facility. This challenge draws from real-world nuclear security frameworks established by the **Nuclear Regulatory Commission (NRC)** and the **International Atomic Energy Agency (IAEA)**.

Your goal is to achieve an balance between security and operational efficiency. A system that stops every threat but paralyzes daily operations is an engineering failure; conversely, a system that prioritizes convenience at the expense of security is a risk.

---

## Challenge Objectives

To complete the challenge, you must configure the facility's security settings to accomplish the following:

* **Establish Security Zones:** Group the physical rooms of the facility into distinct, logical security perimeters.
* **Define Access Permissions:** Assign explicit clearance levels for every personnel role across each security zone.
* **Implement Conditional Controls:** Apply secondary security requirements where vulnerabilities exist.
* **Configure State-Dependent Logic:** Program how access permissions dynamically modify when the facility transitions from Normal Operations to an Emergency/Alert State.
* **Provide Engineering Justification:** Defend your architectural decisions based on established nuclear security principles.

---

## Workflow

1. **Design Phase:** Use the dashboard to map rooms to zones and assign role clearances. The interface will save your progress directly to your local workspace files.
2. **Dynamic Scenario Phase:** The system will present real-world operational edge cases. You must evaluate how your programmed rules respond to these scenario injects.
3. **Simulation Phase:** Once finalized, run the simulation tool to subject your access policy to automated adversary testing profiles.
4. **Iterative Optimization:** Review the generated performance logs, identify vulnerabilities, adjust your configuration in the interface, and resubmit for evaluation.

---

## Environment & Materials

### Workspace File Structure

Your project directory contains the following configuration and documentation files:

```text
smr_challenge/
├── data/
│   └── facility_blueprint.json   # Read-only physical layout and role requirements
├── policies/
│   └── policy_config.json        # Output file managed and updated by the interface
└── docs/
    └── justification.md          # Engineering design report template

```

### What is Provided

* **Facility Blueprint Data:** A layout mapping the physical rooms, structural doors, and directional connections of the SMR facility.
* **Personnel Profiles:** Operational definitions for six core facility roles (Reactor Operator, Security Officer, Maintenance Technician, Contractor, Visitor, and Emergency Responder).
* **Core Mission Requirements:** The baseline rooms each personnel role must be capable of reaching to execute their mandatory daily duties.

### What Needs to Be Submitted

1. **`policy_config.json`:** The finalized permission matrix and zone topography exported via the graphical interface.
2. **`justification.md`:** A completed engineering report defending your design choices, zone boundaries, and state-dependent logic.

---

## Evaluation Criteria

Your submission will be automatically evaluated across three core engineering metrics:

| Metric | Evaluation Focus |
| --- | --- |
| **Security Effectiveness** | The defensive capability of your policy when evaluated against automated adversary simulation profiles. |
| **Operational Feasibility** | The structural viability of your layout. Personnel must be able to perform required duties without systemic deadlock. |
| **Architectural Rigor** | The technical validity and depth of your engineering justifications in the submitted design documentation. |

---

## Recommended Research Concepts

To maximize the effectiveness of your design, it is highly recommended to research the following nuclear industry security concepts before beginning construction:

* **Defense-in-Depth (Physical Application)**
* **Design Basis Threat (DBT)**
* **Vital Area Identification (VAI)**
* **The Principle of Least Privilege**
* **The Detection, Delay, and Response Triad**
* **Two-Person Rule (M-of-N Authentication)**
* **Access Control List (ACL) Fail-Secure Mechanics**
