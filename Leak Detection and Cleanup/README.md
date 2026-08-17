# Leak Detection and Cleanup

Leak detection is an essential component of safe nuclear facility operation, as abnormal releases can severely affect containment, operating conditions, and response actions. Small Modular Reactors (SMRs) present unique detection challenges due to their compact form factor, novel geometries, and distributed deployment scenarios compared to traditional large reactors.

This subchallenge invites teams to develop autonomous systems capable of detecting, localizing, and reporting abnormal leakage conditions in SMR facilities. Solving this problem empowers operators with rapid situational awareness, minimizes contamination spread, and supports automated cleanup operations through robotics, sensor networks, data analysis, and machine learning.

---

## Table of Contents

- [Challenge](#challenge)
- [Potential Solutions](#potential-solutions)
- [Resources](#resources)

---

## Challenge

Your goal is to develop solutions that address autonomous leak detection, localization, contamination tracking, and response in SMR nuclear facilities.

Successful solutions should consider:

- Accounting for diverse leak types, including primary heat transport system (PHTS) leaks and failed-fuel fission product releases.
- Monitoring contamination spread in real time and supporting cleanup operations.
- Integrating modern sensor technology, AI/ML models, robotics, and simulation to reason about facility safety.

Teams are encouraged to explore solutions such as:

- Software applications (e.g., real-time dashboards, alert systems, and data processing pipelines)
- Hardware & Sensor Networks (e.g., multi-point sensor arrays, calibration profiles, and triangulation algorithms)
- Machine Learning approaches (e.g., time-series classification models for operational state recognition)
- Autonomous Robotics (e.g., drones or ground robots for facility patrol and search routing)
- Physics-Based Modeling (e.g., radiation transport analysis and signal fusion for source identification)

Solutions should consider:

- Feasibility
- Scalability
- User impact (operator response time, safety, and operational awareness)
- Sustainability
- Technical implementation (model generalization, sensor noise/calibration, and spatial navigation)

---

## Potential Solutions

The supported solutions below provide working materials that teams can build on. The extension ideas show ways to develop those starting points further. The additional possibilities are independent ideas that teams may pursue from scratch or combine with a supported solution.

### Supported Solutions

| Supported Solution | Possible Directions | Resources |
| --- | --- | --- |
| **AI leak-detection model** | Train a model that identifies leaks from time-series sensor data. | [ML framework notebook](machine_learning/) |
| **Simulated-vibration localization system** | Use a simple containment structure and simulated vibration readings to locate modelled leaks. | [Sensor localization tools](sensor_localization/) |
| **Digital facility patrol simulation\*** | Program a drone or robot to search a simulated facility for leaks. | [3D simulation environment](leak-detection-simulation/) |

*\*The Drone Simulation solution was created in an older version of Godot and may need to be updated to work properly. It is advised you only choose this solution if you have experience with game engines.*

### Ways to Extend the Supported Solutions

| Extension | Description |
| --- | --- |
| **Real-time operator alert dashboard** | Visualize sensor data streams, estimated leak coordinates, contamination maps, and operational anomalies from one or more supported solutions. |
| **Sensor fusion and calibration** | Combine noisy readings from multiple sensors, account for calibration differences, and compare localization accuracy under different sensor arrangements. |
| **False-alarm filtering** | Extend the AI leak-detection model to distinguish leak signatures from normal operating changes, sensor noise, and other non-leak events. |
| **Contamination mapping** | Extend the digital patrol simulation so a drone or robot records readings, estimates the affected area, and updates a facility map as it moves. |

### Additional Possibilities

| Perspective | Possibility |
| --- | --- |
| Engineering | Develop a **sensor-integrated pipe sleeve** that continuously monitors piping and joints. |
| Engineering | Design a **drone-based facility inspection system** that uses cameras and environmental sensors in difficult-to-access spaces. |
| Science | Conduct a **coolant leak dispersion experiment** using safe surrogate fluids to study how leaks spread through narrow SMR geometries. |
| Science | Perform **early leak signature characterization** to determine which physical indicators appear first as a leak develops. |
| Science | Complete a **thermal plume mapping study** investigating heat patterns around small leaks. |
| Science | Run a **tracer-based leak tracking investigation** using dyes or tracers to study migration through confined systems. |
| Science | Conduct **sensor placement optimization research** to identify effective sensor configurations for compact SMR layouts. |
| Science | Perform a **material-defect leakage study** exploring how crack size, shape, and orientation affect leak rates. |
| Science | Complete a **comparative evaluation of leak-detection technologies** including acoustic, thermal, pressure, chemical, and radiation-based methods. |
| Science | Carry out a **machine-learning analysis of leak scenarios** to determine whether sensor patterns can distinguish different leak types. |
| Science | Develop an **environmental transport model** investigating how contaminants move through ventilation systems and enclosed spaces. |
| Science | Build a **cleanup effectiveness evaluation platform** that compares cleanup and containment materials. |

---

## Resources

The following resources may help teams better understand the problem and develop solutions.

### Background Information

- **IAEA Safety Standards:** [Radiation Protection and Safety of Radiation Sources (GSR Part 3)](https://www-pub.iaea.org/mtcd/publications/pdf/pub1578_web-57265295.pdf)
- **Radiation Transport Physics:** Fundamentals of radiation attenuation, inverse-square law, and multi-sensor triangulation for point-source localization.
- **PHTS & Failed-Fuel Leaks:** Understanding primary heat transport system fluid dynamics and fission product transport mechanisms.

### Technical Resources

- **Godot 3D Engine (v4.4+):** [Godot Engine Documentation & GDScript Guide](https://docs.godotengine.org/en/stable/)
- **Machine Learning Frameworks:** [TensorFlow / Keras Documentation](https://www.tensorflow.org/) & [scikit-learn User Guide](https://scikit-learn.org/)
- **Robotics Integration:** [ROS 2 (Robot Operating System) Documentation](https://docs.ros.org/) for advanced robotic mapping and navigation
- **Sensor Localization Module:** [Local Sensor Localization Tools & Algorithms](sensor_localization)
- **Facility Simulation Workspace:** [Local Godot 3D Simulation Environment](leak-detection-simulation)

### Data Sources

- **Time-Series Sensor Dataset:** Preprocessed normal operations and leak event datasets located in [machine_learning/](machine_learning)
- **Sensor Calibration Profiles:** Multi-intensity level (0-100%) sensor calibration profiles located in [sensor_localization/](sensor_localization/sensor_location/calibration/)

### Additional References

- **Sensor Placement Optimization:** Strategies for minimizing blind spots and false alarms across complex, compact reactor geometries.
- **Signal Fusion & Triangulation:** Mathematical frameworks for combining noisy multi-point sensor arrays to estimate source coordinates.
- **Data Processing Pipelines:** Methods for cleaning, filtering, and extracting features from raw time-series sensor streams.
