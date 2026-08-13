# Security

Small Modular Reactors (SMRs) represent the next generation of nuclear energy, featuring compact designs, factory fabrication, and passive safety systems. However, their smaller physical footprints introduce unique security challenges.

Your task is to design a **Physical Protection System (PPS)** that safeguards a fictional SMR facility against radiological sabotage and the theft of sensitive materials, while remaining operationally viable. Solutions must balance security effectiveness against operational feasibility: a system that stops every threat but paralyzes daily operations is an engineering failure, while a system that prioritizes convenience at the expense of security is a major risk.

This challenge draws from real-world nuclear security frameworks established by key regulatory stakeholders, including the **Nuclear Regulatory Commission (NRC)** and the **International Atomic Energy Agency (IAEA)**.

---

## Table of Contents

- [Challenge](#challenge)
- [Potential Solutions](#potential-solutions)
- [Resources](#resources)

---

## Challenge

Your goal is to develop solutions that address physical security policy and access control design for a modern SMR facility.

Successful solutions should consider:

- Safeguarding vital facility areas against radiological sabotage and theft of sensitive nuclear materials.
- Detecting unauthorized removal of radiological or nuclear material from the premises, in addition to preventing unauthorized entry.
- Balancing physical security enforcement with daily operational efficiency and facility access.
- Incorporating established nuclear security principles from regulatory frameworks like the NRC and IAEA.

Teams are encouraged to explore solutions such as:

- Software applications (e.g., policy simulation dashboards)
- Hardware prototypes (e.g., physical access circuits and badge readers)
- Computer vision approaches (e.g., automated perimeter and intrusion detection)
- Facility optimization methods (e.g., spatial layout redesigns for sightlines and barrier placement)

Solutions should consider:

- Feasibility
- Scalability
- User impact (operational staff workflow and safety)
- Sustainability
- Technical implementation & fail-secure mechanics

---

## Potential Solutions

The supported solutions below provide working materials or a defined walkthrough that teams can build on. The extension ideas show ways to develop those starting points further. The additional possibilities are independent ideas that teams may pursue from scratch or combine with a supported solution.

### Supported Solutions

| Supported Solution | Possible Directions | Resources |
| --- | --- | --- |
| **Security policy-simulation dashboard** | Design zones and access rules and test them against simulated adversary profiles. | [Policy simulation walkthrough](policy_simulation/README.md) |
| **Physical access hardware** | Prototype NFC or RFID badge readers and fail-secure mechanics. | [Hardware walkthrough](policy_simulation/README.md) |
| **Computer-vision intrusion detection** | Detect movement in restricted areas and integrate detections with alarms. | [OpenCV documentation](https://docs.opencv.org/) |

### Ways to Extend the Supported Solutions

| Extension | Description |
| --- | --- |
| **Facility layout testing** | Extend the policy simulation to compare sightlines, security zones, detector coverage, and physical barrier placement. |
| **Alarm response integration** | Connect a detection event to lockdown, notification, or two-person verification procedures in the policy simulation. |
| **Live hardware integration** | Feed NFC or RFID badge-reader events into the dashboard and verify that software policies and physical access controls agree. |
| **Computer-vision scenario testing** | Test intrusion detection against different personnel movements, restricted areas, lighting conditions, and nuisance events. |

### Additional Possibilities

| Perspective | Possibility |
| --- | --- |
| Engineering | Create a **critical-sensor integrity monitoring system** that detects manipulation or malfunction. |
| Engineering | Build an **operational anomaly-detection platform** that identifies unusual data across plant systems. |
| Science | Perform a **security-sensor technology assessment** comparing thermal imaging, cameras, acoustic systems, and environmental sensors. |
| Science | Conduct a **facility layout and detection coverage study** to improve security effectiveness. |
| Science | Study **environmental indicators of unusual activity** that could improve situational awareness. |
| Science | Assess **radiological hazard and material monitoring** at entrances, exits, and other key zones. |
| Science | Investigate **false-alarm reduction methods** that improve detection without causing alarm fatigue. |

### Developing the Additional Possibilities

The additional possibilities do not have complete repository solutions. Teams can treat them as standalone contributions or connect them to a supported solution—for example, by feeding a sensor-integrity alert into the policy-simulation dashboard. Possible directions include:

- **Radiation portal monitoring:** Simulate or prototype gamma or neutron detection at facility exit points to flag material leaving without authorization.
- **Sensor placement strategy:** Model where detectors should be sited to maximize detection probability while minimizing false alarms and traffic bottlenecks.
- **Alarm response integration:** Design how a detection event would trigger lockdown, notification, or two-person verification procedures, tying back into the Detection, Delay, and Response triad described below.
- **Nuisance-alarm mitigation:** Consider how naturally occurring radioactive material (NORM) or medical isotopes carried by personnel could be filtered out to avoid alarm fatigue.

---

## Resources

The following resources may help teams better understand the problem and develop solutions.

### Background Information

- **IAEA Nuclear Security Series No. 13:** [Recommendations on Physical Protection of Nuclear Material and Facilities](https://www-pub.iaea.org/MTCD/Publications/PDF/Pub1481_web.pdf)
- **U.S. NRC 10 CFR 73.55:** [Requirements for Physical Protection of Licensed Activities in Nuclear Power Reactors](https://www.ecfr.gov/current/title-10/chapter-I/part-73/subpart-F/section-73.55)
- **U.S. NRC 10 CFR 73.1:** [Design Basis Threat (DBT) Framework](https://www.ecfr.gov/current/title-10/chapter-I/part-73/subpart-A/section-73.1)
- **Defense-in-Depth (Physical Application):** Applying multiple independent layers of security so no single point of failure compromises the facility.
- **Vital Area Identification (VAI):** Systematic identification of critical facility areas where compromise could enable sabotage.

### Technical Resources

- **Proposed Solution Walkthrough:** [Step-by-Step Setup & Execution Guide](policy_simulation/README.md)
- **Submission Guidelines:** [Presentation and Submission](../README.md#presentation-and-submission)
- **Judging Criteria:** [Judging Criteria](../README.md#judging-criteria)
- **NFC Hardware Integration:** [PN532 NFC Module Library & Arduino/ESP32 Guides](https://github.com/elechouse/NFC_PN532)
- **Computer Vision Tools:** [OpenCV Computer Vision Library](https://opencv.org/)
- **Radiation Detection Basics:** [NRC Radiation Portal Monitors & Detection Overview](https://www.nrc.gov/about-nrc/radiation/health-effects/detection-radiation)

### Data Sources

- **Facility Map Layout:** [Facility Layout Map Asset](policy_simulation/assets/facility_map.png)
- **Simulation Dashboard Logs:** Available inside the [Policy Simulation Package](policy_simulation/README.md)

### Additional References

- **Principle of Least Privilege:** Restricting user and role access to only the minimum privileges needed to perform operational duties.
- **The Detection, Delay, and Response Triad:** A core physical security framework combining early intrusion detection, physical delay mechanisms, and response procedures.
- **Two-Person Rule (M-of-N Authentication):** Requiring dual authorization for high-risk or critical actions to mitigate insider threats.
- **ACL Fail-Secure Mechanics:** Ensuring physical and software access control systems default to denial ("fail closed") upon system failure or power loss.
- **Radiation Portal Monitoring:** Fixed detection points (e.g., at exits and vehicle gates) that screen for gamma or neutron emissions to help identify material leaving a facility without authorization.
- **Nuisance Alarm Rate:** A key design tradeoff in radiation detection systems — sensitivity high enough to catch real threats without triggering excessive false alarms from background sources or medical isotopes.
- **Sandia National Laboratories:** [Physical Protection System (PPS) Engineering Principles](https://www.sandia.gov/)
