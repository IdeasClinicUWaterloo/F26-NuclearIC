# Welcome to the 2026 Nuclear Innovation Challenge!

Created by Engineering IDEAs Clinic co-op students.

## Accessibility

This README uses descriptive headings, meaningful link names, short sections, and alt text for images so it is easier to navigate with screen readers and other assistive technologies. The challenge also welcomes accessible solutions that work for people with different needs and levels of technical experience.

## Table of Contents

- [Accessibility](#accessibility)
- [Quick Links](#quick-links)
- [Your Mission](#your-mission)
- [Sub-Problems](#sub-problems)
  - [Controls and Instrumentation](#controls-and-instrumentation)
  - [Leak Detection and Cleanup](#leak-detection-and-cleanup)
  - [Reactor Design Optimization](#reactor-design-optimization)
  - [Security](#security)
- [General Resources](#general-resources)
  - [Presentation and Submission](#presentation-and-submission)
  - [Judging Criteria](#judging-criteria)
  - [Schedule](#schedule)

## Quick Links

- [BWRX-300 Small Modular Reactor](https://www.gevernova.com/nuclear/carbon-free-power/bwrx-300-small-modular-reactor)
- [Controls and Instrumentation Subproblem](Controls%20and%20Instrumentation/)
- [Leak Detection and Cleanup Subproblem](Leak%20Detection%20and%20Cleanup/)
- [Reactor Design Optimization Subproblem](Reactor%20Design%20Optimization/)
- [Security Subproblem](Security/)


### Theme: Small Modular Reactors (SMRs)


![Chart explaining the components and operation of a small modular reactor](assets/SMR_Chart.png)

## Background

As technology advances to embrace Artificial Intelligence (AI), data centres have become major energy consumers. To provide the energy output demanded by data centres, alternative energy-production options need to be considered. Small Modular Reactors (SMRs) are at the forefront of these conversations, with multiple designs being developed to address these energy needs. The Darlington New Nuclear Project is an SMR project under construction in Ontario and is expected to become the first grid-scale SMR in the G7. Construction began in May 2025, with completion expected by the end of the decade and connection to the electricity grid expected by the end of 2030.

The Darlington project uses the GE Vernova Hitachi BWRX-300 boiling water reactor (BWR). The BWR uses nuclear fission to turn water into steam, which goes directly to a turbine to create electricity. Construction of the four planned units is expected to create up to 18,000 jobs. Their construction, operation, and maintenance are expected to add $38.5 billion to Canada's GDP over 65 years. Together, the four units will provide 1,200 megawatts of electricity, enough to power approximately 1.2 million homes.

To find out more: [BWRX-300 SMR](https://www.gevernova.com/nuclear/carbon-free-power/bwrx-300-small-modular-reactor)

For a broader view of SMR design, see the [OECD-NEA SMR Dashboard](https://www.oecd-nea.org/upload/docs/application/pdf/2025-09/web_-_smr_dashboard_-_third_edition.pdf) and the [IAEA ARIS SMR Catalogue](https://aris.iaea.org/Publications/SMR_catalogue_2024.pdf). Both give a sense of the variety of SMR designs being developed internationally. You can find the BWRX-300 on page 134 of the OECD Dashboard and page 17 of the IAEA Catalogue.


## Your Mission
In this challenge, your team has been invited to build a solution to improve SMRs in some way. You may extend the supplied code and hardware designs, combine ideas from several sub-problems, or create a related solution of your own. Your solution should be catered towards a real SMR - the BWRX-300 or any other you may be interested in.

As this is an interdisciplinary challenge, solutions should combine scientific thinking and engineering
design. Your solutions can take many forms, including a Prototype, a Model, a Proposal, an Experiment etc. The
balance between science and engineering can vary in the solutions as long as a threshold of
20% engineering and 20% science is surpassed. Your output by the end of the weekend should convince the judges that your solution is feasible, safe, and secure.

As you make your solution this weekend, use the  [judging criteria](#judging-criteria) to guide your decisions and demonstration.

#### Team Formation 

Your team should comprise of 3-5 students with a close-to even split between students from the Science Faculty and students from the Engineering Faculty.

---

## Sub-Problems

### Controls and Instrumentation

Modern energy systems rely on sensors, controllers, and safety systems to operate reliably. In nuclear power plants, instrumentation and control systems help monitor reactor power, temperature, coolant conditions, and control rod movement to keep the system stable and safe.

This challenge invites students to develop or improve a control and instrumentation solution for an SMR-inspired system. Teams may build on one of the supported solutions, create something new from scratch, or develop something inspired by the supported solutions without directly extending them.

Projects may take the form of software, hardware, experiments, simulations, data analysis, or research. Solutions should explore how measurements, control decisions, physical behaviour, and human operators interact when sensors are noisy, disturbances occur, components fail, or safety limits are approached.

#### Potential Solutions

| Engineering Perspective | Science Perspective |
|---|---|
|&bull; Use the **supported simulated reactor track** to improve control, fault detection, safety, estimation, or visualization.[[Supported]](Controls%20and%20Instrumentation/) <br>&bull; Use the **supported physical analogue track** to build a temperature, dye, pump, or flow system that demonstrates feedback and safety.[[Supported]](Controls%20and%20Instrumentation/) <br>&bull; Create a **digital reactor control-room simulator** that displays reactor conditions, controls, alarms, and safety state.<br>&bull; Develop an **autonomous control-rod optimization tool** that recommends safe rod movements.<br>&bull; Build a **wireless auxiliary-system sensor network** that monitors pumps, valves, temperature, or flow.<br>&bull; Design a **redundant sensor validation architecture** that identifies incorrect measurements.<br>&bull; Build a **portable instrumentation training rig** that demonstrates measurement, control, alarms, and shutdowns.|&bull; Use the **supported simulated reactor track** to study reactor kinetics, heat transfer, uncertainty, power, temperature, and reactivity.[[Supported]](Controls%20and%20Instrumentation/) <br>&bull; Use the **supported physical analogue track** to study temperature, flow, mixing, sensor accuracy, and system response. [[Supported]](Controls%20and%20Instrumentation/) <br>&bull; Develop a **smart sensor health monitoring system** that detects noise, drift, and failures.<br>&bull; Create a **digital twin of an SMR cooling loop** to model coolant flow and heat transfer.<br>&bull; Design a **predictive instrumentation maintenance platform** that anticipates instrument failures.<br>&bull; Develop an **AI-assisted alarm prioritization system** that groups and ranks alarms during abnormal conditions.<br>&bull; Conduct a **human-factors control-panel redesign** that applies cognitive science to reduce operator mistakes.|

Learn more in the [Controls and Instrumentation subproblem](Controls%20and%20Instrumentation/).

### Leak Detection and Cleanup

A big concern in any nuclear facility is quickly detecting leaks. SMRs face additional concerns compared to traditional reactors because of their different geometry and narrow form factor.

This challenge invites students to develop a system capable of autonomously detecting, localizing, and reporting radiation leaks in SMR facilities. Solutions may also include methods for monitoring contamination spread and supporting cleanup operations.

#### Potential Solutions

| Engineering Perspective | Science Perspective |
|---|---|
|&bull; Train an **AI leak-detection model** that identifies leaks from sensor data.[[Supported]](Leak%20Detection%20and%20Cleanup/) <br>&bull; Build a **simulated-vibration localization system** that uses a simple containment structure to locate modelled leaks.[[Supported]](Leak%20Detection%20and%20Cleanup/) <br>&bull; Create a **digital facility patrol simulation** with a drone or robot searching for leaks.[[Supported]](Leak%20Detection%20and%20Cleanup/) <br>&bull; Develop a **sensor-integrated pipe sleeve** that continuously monitors piping and joints.<br>&bull; Design a **drone-based facility inspection system** that uses cameras and environmental sensors in difficult-to-access spaces.|&bull; Conduct a **coolant leak dispersion experiment** using safe surrogate fluids to study how leaks spread through narrow SMR geometries.<br>&bull; Perform **early leak signature characterization** to determine which physical indicators appear first as a leak develops.<br>&bull; Complete a **thermal plume mapping study** investigating heat patterns around small leaks.<br>&bull; Run a **tracer-based leak tracking investigation** using dyes or tracers to study migration through confined systems.<br>&bull; Conduct **sensor placement optimization research** to identify effective sensor configurations for compact SMR layouts.<br>&bull; Perform a **material-defect leakage study** exploring how crack size, shape, and orientation affect leak rates.<br>&bull; Complete a **comparative evaluation of leak-detection technologies** including acoustic, thermal, pressure, chemical, and radiation-based methods.<br>&bull; Carry out a **machine-learning analysis of leak scenarios** to determine whether sensor patterns can distinguish different leak types.<br>&bull; Develop an **environmental transport model** investigating how contaminants move through ventilation systems and enclosed spaces.<br>&bull; Build a **cleanup effectiveness evaluation platform** that compares cleanup and containment materials.|

Learn more in the [Leak Detection and Cleanup subproblem](Leak%20Detection%20and%20Cleanup/).

### Reactor Design Optimization

SMRs are a relatively new technology that have some advantages over traditional nuclear reactors, but also some disadvantages. A major part of designing SMRs is optimizing their design to minimize their disadvantages and maximize their advantages. There are many parts of a reactor that can affect efficiency, cost, and feasibility of the design. Reactor performance depends on design choices such as fuel rod geometry and material selection, and operating choices such as control rod movement, coolant flow, steam flow, and startup strategy.

This challenge invites students to use physics and engineering principles to model a reactor that is efficient, economical, and practical for deployment. Solutions should explore trade-offs among fuel design, reactor performance, lifecycle cost, and operational constraints. Teams may focus on reactor design optimization, reactor operation optimization, or a combination of both. The goal is to improve performance while considering safety limits, power output, fuel lifetime, cost, and overall system efficiency.

Participants are encouraged to build tools, simulations, dashboards, or algorithms that compare design choices, tune operating strategies, or automatically search for better solutions.

#### Potential Solutions

| Engineering Perspective | Science Perspective |
|---|---|
|&bull; Use the provided **SMR Reactor Design Optimization Tool** to set parameters and examine their effects on reactor cost and efficiency.[[Supported](Reactor%20Design%20Optimization/) <br>&bull; Develop an **automated reactor controller** that reads the live state of a simulator and adjusts control values to maximize efficiency.[[Supported](Reactor%20Design%20Optimization/) <br>&bull; Apply **reactor optimization methods** to improve startup, tracking, recovery, or design performance.<br>&bull; Create a **reactor comparison dashboard** for designs, simulator runs, costs, and performance metrics.<br>&bull; Build a **reactor data analysis system** to identify which design or control parameters affect performance most.<br>&bull; Research an **SMR design concept** and develop a proposal for a particular reactor design.|&bull; Conduct a **reactor-channel flow investigation** using safe surrogate systems to model coolant movement and heat removal through reactor channels.<br>&bull; Create a **cost optimization** strategy for the plant <br>&bull; Perform a **component lifespan study** examining how temperature, flow, load cycles, and other operating conditions influence longevity.<br>&bull; Create a **reactor efficiency map** relating coolant flow, temperature, and power output to identify efficient operating ranges.<br>&bull; Complete a **reactor lifecycle optimization study** examining how design choices affect long-term performance, maintenance needs, and operating efficiency.|

Learn more in the [Reactor Design Optimization subproblem](Reactor%20Design%20Optimization/).

### Security

Nuclear facilities are highly critical locations that require extremely strict security measures to prevent sabotage. Nuclear facilities integrate multi-layered security protocols and policies to protect the premises from bad actors. SMR facilities may need to diverge from the traditional reactor structure, which may introduce new security concerns.

This challenge asks teams to design access-control policies, detection strategies, and response workflows that safeguard vital areas, detect unauthorized removal of radiological material, and mitigate insider or external threats without causing excessive nuisance alarms or operational paralysis.

#### Potential Solutions

| Engineering Perspective | Science Perspective |
|---|---|
|&bull; Build a **security policy-simulation dashboard** to design zones and access rules and test them against adversary profiles.[[Supported]](Security/) <br>&bull; Prototype **physical access hardware** using NFC or RFID badge readers and fail-secure mechanics.[[Supported]](Security/) <br>&bull; Develop **computer-vision intrusion detection** for restricted areas and integrate it with alarms.[[Supported]](Security/) <br>&bull; Create a **critical-sensor integrity monitoring system** that detects manipulation or malfunction.<br>&bull; Build an **operational anomaly-detection platform** that identifies unusual data across plant systems.|&bull; Perform a **security-sensor technology assessment** comparing thermal imaging, cameras, acoustic systems, and environmental sensors.<br>&bull; Conduct a **facility layout and detection coverage study** to improve security effectiveness.<br>&bull; Study **environmental indicators of unusual activity** that could improve situational awareness.<br>&bull; Assess **radiological hazard and material monitoring** at entrances, exits, and other key zones.<br>&bull; Investigate **false-alarm reduction methods** that improve detection without causing alarm fatigue.|


Learn more in the [Security subproblem](Security/).

---

## General Resources

Resources and kit information can be found in the folder for each subproblem.

To sign out a kit, go to the sign-out table and speak to a co-op student. You will have to complete safety training for some of the kits.

### Presentation and Submission

Teams will give a short presentation of about 3 to 5 minutes. Include:

- the problem you chose and who it affects
- how your solution works
- the prototype, simulation, dashboard, research, or hardware demonstration
- the safety constraints and edge cases you considered
- the result you achieved
- what you would improve with more time

Your submission may include code, a dashboard, a simulation, a hardware and software demonstration, a design with partial implementation, a research-based proposal, or a combination of these.

### Schedule

**Location**: IDEAs Clinic room (E7-1427)

**Prep Session**: October 2 (Fri), 5:30 PM - 8:00 PM
Here you will introduced to the problem and the tools you will have to solve it. You will also start forming teams.

**Hackathon**: October 3 & 4 (Sat & Sun), 9:00 AM - 5:00 PM
This is the bulk of the mostly freeform design time. You will consult with CNL reps and put together your solutions.
Judging will begin around 2:30pm on Sunday.

### Judging Criteria


#### Ideation
| Category | What judges are looking for | Score |
| --- | --- | --- |
| **Integration of Engineering and Science** | Is there at least 20% Engineering and at least 20% Science in each solution? | /10 |
| **Relevance** | How relevant is the solution to the problem space? | /3 |
| **Feasibility** | How feasible is the solution? | /3 |
| **Impact** | How positively does the idea impact stakeholders? | /3 |


#### Quality of Output
| Category | What judges are looking for | Score |
| --- | --- | --- |
| **Quality of Output** | At the time of judging, how put-together is the prototype, model, proposal, etc.? | /5 |
| **Strength of Evidence** | How solid is the evidence for the proposed solution? Examples include literature review, calculations, and experimental results. | /5 |
| **Representation of Final Solution** | How representative of the final solution is the output of the weekend? | /5 |

#### Safety & Regulations
| Category | What judges are looking for | Score |
| --- | --- | --- |
| **Public Safety Considerations** | Are risks to the general public recognized and addressed? | /3 |
| **Employee / Operator Safety** | Does the design account for risks to workers/users, such as ergonomics, exposure, and radiation safety? | /3 |
| **Regulatory Awareness** | Has the team identified relevant Canadian regulations, such as CNSC requirements, the Nuclear Safety and Control Act, and Packaging and Transport Regulations? | /3 |

#### Security
| Category | What judges are looking for | Score |
| --- | --- | --- |
| **Threat Awareness** | Has the team identified risks from misuse or bad actors? | /3 |
| **Mitigation Measures** | How effective are the proposed protections, such as access control, fail-safes, and monitoring? | /3 |
| **Transparency vs. Security** | Does the design responsibly balance openness and public transparency with the need for security? | /3 |

#### Demo / Pitch / Presentation
| Category | What judges are looking for | Score |
| --- | --- | --- |
| **Clarity** | How clear was the presentation in terms of explanation? | /5 |
| **Depth** | Was the extent of the team's knowledge thoroughly expressed? | /5 |
| **Demo** | How well designed was the demonstration? Was it an impactful way to demonstrate what the team tried to accomplish? | /5 |



