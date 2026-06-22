# Leak Detection and Cleanup

## Challenge Description

A critical concern in any nuclear facility is the rapid and accurate detection of radiation leaks. Small Modular Reactors (SMRs) present unique leak detection challenges due to their compact form factor, novel geometries, and distributed deployment scenarios compared to traditional large reactors. Early leak identification is essential to contain contamination, minimize exposure, and enable swift remediation.

This subchallenge invites students to develop autonomous systems capable of detecting, localizing, and reporting radiation leaks in SMR facilities. Solutions may also address monitoring contamination spread and supporting cleanup operations through robotics, sensor networks, data analysis, and machine learning techniques.

The goal is not to build a production-grade radiological monitoring system, but to explore how modern sensor technology, AI, robotics, and simulation can be integrated to address real-world nuclear facility challenges.

## Potential Solutions

Teams may approach this challenge in several ways, depending on their background and interests:

- **Train a machine learning model** to classify normal operations versus leak events using multivariate sensor time-series data
- **Develop a sensor localization algorithm** to triangulate or estimate the spatial origin of a detected leak using multiple sensor readings
- **Build or extend the 3D simulation environment** to model drone or robot patrol paths that optimize coverage and response time
- **Create a data acquisition and preprocessing pipeline** to clean sensor data, extract features, and prepare training datasets for ML models
- **Design a real-time decision system** that triggers alerts, coordinates robotic response, and guides cleanup teams
- **Perform sensitivity analysis** on sensor placement and model hyperparameters to optimize leak detection accuracy and false alarm rates
- **Build a dashboard or monitoring interface** that displays sensor health, leak probability, localization estimates, and facility status

## Proposed Solution Components

This challenge is supported by three integrated subsystems:

### 1. Leak Detection Simulation (3D Environment)
Located in `leak-detection-simulation/`, a Godot-based 3D environment models a nuclear facility with:
- Spatial layout and containment structures
- Simulated drone or mobile robot for facility inspection
- Fog volume rendering to represent contamination spread
- Real-time sensor visualization and navigation

**Key features:**
- Autonomous pathfinding and patrol logic
- Dynamic environmental effects (fog, particles)
- Integration with external sensor data sources

**Next steps:**
- Extend robot behavior with leak detection and response heuristics
- Add realistic environmental models and sensor simulation
- Create scenario-based testing with injected leak events

### 2. Machine Learning Leak Detection (Data Analysis)
Located in `machine_learning/`, a Jupyter notebook framework for training and evaluating leak detection models:
- Data preprocessing and windowing for time-series classification
- Feature extraction from multi-channel sensor data
- Neural network model design and training
- Performance evaluation using confusion matrices and classification reports

**Supported data types:**
- Normal operations, transient accidents (non-leak), and leak events (LOCA, SGATR scenarios)
- Time-stamped multivariate sensor readings

**Next steps:**
- Tune model hyperparameters and architecture
- Compare against baseline classifiers
- Test generalization on new facility configurations
- Deploy model inference in real-time systems

### 3. Sensor Localization (Source Identification)
Located in `sensor_localization/`, algorithms for determining leak origin:
- **read_sensors/**: Raw sensor data collection and streaming
- **sensor_location/**: Localization algorithms and calibration data
  - Multiple calibration profiles (0%, 20%, 40%, 60%, 80%, 100%) for system response curves
  - Python-based triangulation or source-tracking methods

**Key features:**
- Multi-sensor fusion for spatial estimation
- Calibration-based accuracy improvement
- Extensible to new sensor types and facility geometries

**Next steps:**
- Validate localization accuracy against ground-truth leak locations
- Optimize algorithm for latency and computational cost
- Integrate with robotic navigation to prioritize inspection areas

## Recommended Workflow

1. **Understand the Data**: Review the machine learning notebook and sensor localization code to understand available data formats and existing model structure.
2. **Run Baseline Tests**: Execute the ML notebook to train a baseline leak detection model and evaluate performance.
3. **Improve Detection**: Experiment with feature engineering, model architecture, or ensemble methods to improve accuracy.
4. **Develop Localization**: Refine the sensor localization algorithm using calibration data and multi-sensor fusion techniques.
5. **Integrate with Simulation**: Connect your detection and localization pipeline to the 3D environment for end-to-end testing.
6. **Optimize Response**: Design robot patrol paths, alert thresholds, and cleanup prioritization based on simulation results.
7. **Document and Validate**: Create performance reports, test against adversarial scenarios, and justify design choices.

## Environment & Materials

### Workspace File Structure
```
Leak Detection and Cleanup/
├── README.md                           # This file
├── leak-detection-simulation/          # Godot 3D environment
│   ├── project.godot                   # Godot project configuration
│   ├── *.tscn                          # 3D scenes (world, rooms, drone, etc.)
│   ├── *.gd                            # GDScript behavior and control logic
│   ├── shaders/                        # Custom shaders (water, fog, etc.)
│   └── scripts/                        # GDScript utilities
├── machine_learning/                   # ML model training and evaluation
│   └── LeakDetection.ipynb             # Jupyter notebook for leak classification
└── sensor_localization/                # Sensor reading and leak localization
    ├── read_sensors/                   # Raw sensor data acquisition
    └── sensor_location/                # Localization algorithms and calibration
        └── calibration/                # Calibration profiles (0-100%)
```

### Technology Stack
- **3D Simulation**: Godot Engine 4.4+
- **Machine Learning**: TensorFlow/Keras, scikit-learn, NumPy, Pandas
- **Data Processing**: Python, Jupyter Notebook
- **Robotics/Navigation**: GDScript (Godot), potentially ROS for advanced teams

### Dependencies
- Godot Engine (for simulation)
- Python 3.8+
- TensorFlow, scikit-learn, joblib, pandas, numpy (for ML)
- Jupyter Notebook (for interactive development)

## Getting Started

1. **Review the Challenge**: Read this README and the project mission in the main workspace README.
2. **Explore the Simulation**: Open the Godot project and familiarize yourself with the 3D environment and scenes.
3. **Examine the ML Notebook**: Review the LeakDetection.ipynb to understand the data pipeline and model structure.
4. **Understand the Sensors**: Study the sensor_localization code to learn how localization is performed.
5. **Start Building**: Choose a focus area—detection, localization, robotics, or integration—and begin prototyping.

## Evaluation Criteria

Strong solutions will demonstrate:
- **Detection Accuracy**: High sensitivity and specificity in classifying leaks from sensor data
- **Localization Precision**: Ability to accurately pinpoint leak sources using multi-sensor fusion
- **Real-time Performance**: Timely detection and response without excessive computational cost
- **System Integration**: Seamless collaboration between detection, localization, and robotic response components
- **Robustness**: Graceful handling of sensor noise, model uncertainty, and edge cases
- **Documentation**: Clear explanation of design choices, trade-offs, and validation results
