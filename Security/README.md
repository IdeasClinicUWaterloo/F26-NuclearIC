# Security

## Challenge Description

Small Modular Reactors (SMRs) require robust security measures to protect facilities, prevent unauthorized access, and detect cyber threats. This subproblem focuses on security design for SMR facilities.

Teams will work on security challenges that span two key areas: designing physical access control systems that balance operational efficiency with security, and analyzing network event logs to identify and classify cyber attacks. The goal is to understand how to implement security design principles while maintaining operational viability.

## Potential Solutions

Teams may approach the challenge in several ways:

### Physical Security - SMR Plant Security Policy Game
- Design a digital floor map of an SMR facility with multiple security zones
- Define access levels and control mechanisms (biometrics, access cards, passwords)
- Create zone-based access restrictions tailored to different security requirements
- Evaluate the tradeoffs between operational efficiency and security constraints
- Implement both digital and physical models of the security design
- Develop web-based visualization tools for zone planning and access management

### Cybersecurity - Network Attack Detection and Analysis
- Analyze simulated network event logs from an SMR facility to identify attacks
- Classify detected attacks by type and severity
- Propose security rules and access control policies to mitigate vulnerabilities
- Develop anomaly detection scripts based on identified attack patterns
- Evaluate detection coverage and response time
- Create visualizations of network anomalies and threat patterns

## Recommended Roadmap

### Milestone 1: Understand Security Requirements and Baseline Design

Goal: Learn the fundamental security challenges in SMR facilities and establish baseline designs.

Suggested outcomes:

- Research physical security principles and cybersecurity basics for nuclear facilities
- Understand access control models and network security concepts
- Create an initial facility layout with basic access zones
- Analyze a sample network event log to familiarize with attack signatures
- Identify key security vulnerabilities in baseline designs

Good demo: The team can explain the security requirements for a typical SMR facility and identify at least one major vulnerability.

### Milestone 2: Design and Validate Security Zones

Goal: Design effective security zones using a provided facility map and test the design against adversarial scenarios.

Suggested outcomes:

- Use the provided digital floor map of the SMR facility
- Outline security zones with appropriate access levels and control mechanisms (biometrics, access cards, passwords)
- Define access rules for different personnel roles and security clearances
- Test the zone design against malicious actors (NPC simulations) attempting to infiltrate restricted areas
- Iterate on zone layout to block attack paths while maintaining operational efficiency
- Document security decisions and the vulnerabilities they address

Good demo: The team can demonstrate their zone design and explain how their security system prevents NPC actors from reaching critical areas, while still allowing authorized personnel efficient access to their work areas.

### Milestone 3: Implement Cybersecurity Detection

Goal: Build a system to detect and classify cyber attacks in network logs.

Suggested outcomes:

- Analyze provided network event logs to identify attack patterns
- Classify attacks by type (e.g. unauthorized access, data exfiltration, DoS)
- Develop detection rules or scripts to identify anomalies
- Propose security policies to prevent identified attacks
- Test detection accuracy and false positive rates
- Document attack classifications and remediation strategies

Good demo: The team can run their detection system on a test dataset and identify all planted attacks with minimal false alarms.
