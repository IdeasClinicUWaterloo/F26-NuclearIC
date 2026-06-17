# Welcome to the 2026 Nuclear Innovation Challenge!

Created By: Engineering IDEAs Clinic Co-op Students

## Quick Links

# Your Mission

_Theme: Small Modular Reactors (SMRs)_ <br>

![alt text](assets/Darlington.png)

As the technology advances to embrace Artificial Intelligence (AI), data centers have become massive energy consumption sinks. To provide the energy output demanded by data centers, alternative energy production frontiers need to be considered. Small Modular Reactors (SMRs) are at the forefront of this conversations, with multiple being developed to address these energy needs. The Darlington New Nuclear project is a SMR project currently in development in Ontario, marking the first SMR in the Western world. It began construction in May 2025, and is expected to finish in 2029. 

The Darlington project uses the GE Vernova Hitachi BWRX-300 boiling water reactor (BWR). The BWR uses nuclear fission to turn water into steam, which goes directly to a turbine to create electricity. The project is expected to create more than 18 000 jobs, add $38.5 Billion to Canada's GDP, and provide 1.2 Gigawatts of energy between the four planned units, supplying power to over a million homes. 

To find out more: [BWRX-300 SMR](https://www.gevernova.com/nuclear/carbon-free-power/bwrx-300-small-modular-reactor)


# Subproblems

## Controls and Instrumentation

Modern energy systems rely on sensors, controllers, and safety systems to operate reliably. In nuclear power plants, instrumentation and control systems help monitor reactor power, temperature, coolant conditions, and control rod movement to keep the system stable and safe.

This challenge invites students to design a controller for a simplified SMR-inspired reactor simulation. Teams will try to make the reactor follow a requested power output while handling noisy sensors, disturbances, physical limits, and safety rules.

Students may also build a safe physical analogue system, such as a temperature controller, syringe pump, or water-flow controller, to demonstrate the same feedback control ideas in hardware.

### Potential Solutions:

* Build a PID controller to track a target power level
* Filter noisy sensor readings
* Add safety logic for warnings, limits, SCRAM, or shutdown
* Detect faults such as bad sensors, stuck actuators, or cooling problems
* Create a dashboard to show power, temperature, control input, and safety state
* Build a physical analogue such as a temperature control system, syringe pump, or peristaltic pump flow controller

Learn More: [Controls and Instrumentation Subproblem](/Controls%20and%20Intrumentation/)

## Leak Detection and Cleanup

A big concern in any nuclear facility is quickly detecting leaks. SMRs face additional concerns compared to traditional reactors because of their different geometry and narrow form factor. 

This challenge invites students to develop a system capable of autonomously detecting, localizing, and reporting radiation leaks in SMR facilities. Solutions may also include methods for monitoring contamination spread and supporting cleanup operations.

**Potential Solutions:**

- Train an AI model to detect leaks from sensor data
- Use a simple containment structure with simulated vibrations (as a model for leaks) to localize their locations
- Create a digital mock-up of a nuclear facility and simulate a drone/robot patrolling the facility

Learn More: [Leak Detection and Cleanup Subproblem](/Leak%20Detection%20and%20Cleanup/)

## Reactor Design Optimization

SMRs are a relatively new technology that have some advantages over traditional nuclear reactors, but also some disadvantages. A major part of designing SMRs is optimizing their design to minimize their disadvantages and maximize their advantages. There are many parts of a reactor that can affect efficiency, cost, and feasibility of the design. Reactor performance depends on design choices such as fuel rod geometry and material selection, and operating choices such as control rod movement, coolant flow, steam flow, and startup strategy.

This challenge invites students to use physics and engineering principles to model a reactor that is efficient, economical, and practical for deployment. Solutions should explore trade-offs among fuel design, reactor performance, lifecycle cost, and operational constraints. Teams may focus on reactor design optimization, reactor operation optimization, or a combination of both. The goal is to improve performance while considering safety limits, power output, fuel lifetime, cost, and overall system efficiency.

Participants are encouraged to build tools, simulations, dashboards, or algorithms that compare design choices, tune operating strategies, or automatically search for better solutions.

**Potential Solutions:**

- Use the provided SMR Reactor Design Optimization Tool to set parameters and check the effects on the costs and efficiency of the reactor
- Develop an automated controller that reads the live state of a simulated reactor and adjusts control values to maximize efficiency
- Use optimization methods to improve startup, tracking, recovery, or design performance
- Create dashboards to compare reactor designs, simulator runs, costs, and performance metrics
- Log reactor data and analyze which design or control parameters affect performance most
- Research SMR design concepts and draft a proposal for a particular design

Learn More: [Reactor Design Optimization Subproblem](/Reactor%20Design%20Optimation/)

## Security

Nuclear facilities are highly critical locations that require extremely strict security measures to prevent sabotage. Nuclear facilities integrate multi-layered security protocols and policies to protect the premises from bad actors. SMR facilities may need to diverge from the traditional reactor structure, which may introduce new security concerns.

This challenge invites students to develop a security plan or system for the SMR facility. Participants may explore multiple security concepts, including Security Policy, Zone Access, Cybersecurity, Intruder Detection, etc.

**Potential Solutions:**

- Use the provided security simulation dashboard to set zones and policies for a fictional SMR facility and test against various attackers
- Develop a computer vision system to detect intruders
- Integrate Radio Frequency Identification (RFID) or Near Field Communication (NFC) based access restrictions
- Design a layout for an SMR facility that would be more effective than the one provided at repelling attackers

Learn More: [Security Subproblem](/Security/)

# Resources and Kits

Resources and Kit information can be found in the folders for the respective subproblem. 

To sign out a kit, go to the sign out table and speak to a coop. You will have to go through safety training for some of the kits.

# Presentation & Submission
Please find details about the rubric, presentation and submission [here](/Presentation%20&%20Submission/)

## Schedule
