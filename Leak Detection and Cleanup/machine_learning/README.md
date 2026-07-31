# Machine Learning Leak Detection Challenge

Welcome to the Machine Learning Leak Detection Challenge. This repository provides a baseline Supervised Long Short-Term Memory (LSTM) neural network designed to predict leak probabilities from sequential plant sensor data.

The baseline system classifies operational states into normal operation, leak conditions, and non-leak anomalies or accident scenarios. A decision threshold of 70% probability is used to flag a leak event.

---

## Setup and Execution Guide

Follow these steps to set up the environment and run the notebook in Google Colab:

### Step 1: Notebook Initialization
1. Open [Google Colab](https://colab.research.google.com/).
2. Select **File > Open notebook** (`Ctrl + O`) and upload [`LeakDetection.ipynb`](LeakDetection.ipynb).

### Step 2: Repository Setup
1. Open the Colab Command Palette (`Tools > Command Palette` or `Ctrl + Shift + P`).
2. Search for **terminal** and select **Show Terminal**.
3. Execute the following commands in the terminal:
   ```bash
   git clone https://github.com/thu-inet/NuclearPowerPlantAccidentData
   cd NuclearPowerPlantAccidentData/
   ```

### Step 3: Dependency Configuration
1. Open the **Files** sidebar (sixth icon from the top on the left sidebar).
2. Navigate to `NuclearPowerPlantAccidentData/` and open `requirements.txt`.
3. Replace `~=` with `>=` in the first three lines.
4. Change the fourth line to `torch`.
5. Install the updated requirements in the terminal:
   ```bash
   pip install -r requirements.txt
   ```
   *If installation errors occur, run:*
   ```bash
   pip install -r requirements.txt --index-url [https://pypi.org/simple](https://pypi.org/simple) --extra-index-url [https://pytorch.org](https://pytorch.org)
   ```

### Step 4: Training and Inference
1. **Training Cell (Cell 1):** Generates model weights and outputs initial evaluation metrics.
2. **Inference Cell (Cell 2):** Runs predictions on input sequence files and plots leak probability over time.

---

## Working with Althernative Data

* **Changing Operational Scenarios:**
  * Scenario files are located in `NuclearPowerPlantAccidentData/Operation_csv_data/`.
  * Update file references in the `runs` list within Cell 1 to train on different accident types.
  * In Cell 2, modify the dataset path passed to `run_leak_detection()` (e.g., `run_leak_detection(f"{BASE_DIR}LOCA/1.csv")`).
* **Custom Datasets:**
  * Upload custom CSV files via the Colab File Explorer.
  * Ensure `BASE_DIR` paths match the target dataset folder structure.

---

## Project Overview

This repository serves as the starting template for your solution. You are provided with a functional baseline pipeline, but you are encouraged to refine, optimize, or completely replace the architecture.

### Extension Ideas
* **Model Architecture:** Experiment with GRUs, Bidirectional LSTMs, Transformers, or ensemble methods.
* **Multi-Class Classification:** Extend predictions to estimate leak severity levels or flow rates.
* **Real-Time Data Pipeline:** Implement a dynamic pipeline to ingest continuous data streams and display real-time predictions.
* **Dataset Exploration:** Benchmark performance using alternative time-series datasets or synthetic noise profiles.
* **Default Benchmark Dataset:** [NuclearPowerPlantAccidentData (NPPAD)](https://github.com/thu-inet/NuclearPowerPlantAccidentData).

---

## Baseline System Output

The output graphs below illustrate model performance across three primary operating scenarios:

### Normal Operation
Under standard operating conditions, the predicted leak probability remains near ~35%, well below the 70% decision threshold.

![Figure 1: Leak probability vs. time under normal operating conditions](images/fig1_normal_operation.png)

### Leak Condition (e.g., Steam Generator Tube Rupture)
When a leak occurs, the predicted probability rapidly exceeds the 70% threshold (reaching >83%), successfully triggering an alert.

![Figure 2: Leak probability vs. time under leak-inducing conditions](images/fig2_steam_generator_tube_rupture.png)

### Non-Leak Anomaly (e.g., Control Rod Withdrawal)
During non-leak operational anomalies, predicted probability fluctuates (reaching ~62%) but stays under the threshold, avoiding false alarms.

![Figure 3: Leak probability vs. time under non-leak accident conditions](images/fig3_rod_withdrawal.png)

---

## Model Evaluation

Model performance metrics and confusion matrix results:

![Confusion Matrix Screenshot](images/confusion_matrix.png)

---

## Pipeline & Architecture Overview

### Machine Learning Workflow
The end-to-end workflow follows standard operational stages:

![Flowchart of Machine Learning Model](images/ml_flowchart.png)

1. **Problem Formulation:** Binary classification of multi-sensor time-series sequences.
2. **Data Ingestion:** Reading raw CSV files containing operational readings.
3. **Preprocessing:** Feature selection, sliding window generation, train/val/test splits, normalization, and class weighting.
4. **Model Training:** Training sequential layers with validation tracking.
5. **Inference & Output:** Exporting serialized model assets and plotting continuous probabilities over time.

### Model Architecture
The baseline architecture is built using sequential layers:

1. **Input Layer:** Accepts input shapes defined by `(window_size, num_features)`.
2. **LSTM Layer:** Extracts temporal feature representations from sequential sensor streams.
3. **Dropout Layer:** Mitigates overfitting by dropping units during training.
4. **Dense Layer:** Outputs scalar leak probability values.

*Resource:* [Keras Layers Overview](https://keras.io/api/layers/)

---

## Data Preprocessing Pipeline

Proper sequence preprocessing is required before training:

![Data Preprocessing Block Diagram](images/preprocessing_block_diagram.png)

1. **Labeling:** Assign binary target labels (`1` for leak, `0` for non-leak/normal/non-leak anomaly).
2. **Cleaning:** Filter out non-numeric columns.
3. **Feature Intersection:** Align feature schemas across all CSV files by taking the intersection of shared column headers.
4. **Sliding Windows:** Convert continuous time-series data into fixed sequence windows.
5. **Data Splitting:** Split sequence windows into **70% Training (`X_train`, `Y_train`)**, **15% Validation (`X_val`, `Y_val`)**, and **15% Testing (`X_test`, `Y_test`)**.
6. **Normalization:** Scale input features using `StandardScaler`.
7. **Class Balancing:** Apply `compute_class_weight` to address imbalance between normal operations and rare leak instances.

*Resources:*
* [Sliding Window Method in Time Series Analysis](https://www.geeksforgeeks.org/sliding-window-method-in-time-series-analysis/)
* [Scikit-learn Train Test Split Documentation](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.train_test_split.html)

---

## Technical Reference & Dependencies

### Core Technical Concepts
* **Supervised Learning:** The model trains on labeled sensor sequences (`1` for leak, `0` for non-leak).
  * Resource: [GeeksForGeeks: Supervised and Unsupervised Learning](https://www.geeksforgeeks.org/supervised-unsupervised-learning/)
* **RNNs and LSTMs:** Recurrent Neural Networks and Long Short-Term Memory units handle temporal dependencies across sequential data.
  * Resource: [IBM: Recurrent Neural Networks (RNN)](https://www.ibm.com/topics/recurrent-neural-networks)
* **TensorFlow / Keras:**
  * Resource: [TensorFlow Recurrent Neural Network Guide](https://www.tensorflow.org/guide/keras/rnn)

### Tech Stack & Dependencies
* **Execution Platform:** Google Colab (recommended for GPU runtime and standard dependencies)
* **Required Libraries:**
  * `numpy`: Array manipulation
  * `pandas`: CSV data handling and feature extraction
  * `joblib`: Model artifact serialization
  * `scikit-learn`: Feature scaling (`StandardScaler`), class weighting (`compute_class_weight`), and evaluation metrics
    * Resource: [Scikit-learn Documentation](https://scikit-learn.org/stable/)
  * `tensorflow` / `keras`: Neural network construction and training
    * Resource: [TensorFlow API Documentation](https://www.tensorflow.org/api_docs)