# WiFi CSI Research Notebook

> **Author:** Umang
> **Objective:** Understanding WiFi Channel State Information (CSI) from first principles and building a complete CSI-based perception pipeline for autonomous indoor drone navigation.

---

# Table of Contents

1. Introduction
2. Motivation
3. Problem Statement
4. Research Objectives
5. Repository Structure
6. Learning Roadmap


---

# 1. Introduction

Indoor localization and navigation remain challenging problems because traditional Global Navigation Satellite Systems (GNSS), such as GPS, fail indoors due to severe attenuation and multipath propagation. Warehouses, underground parking structures, factories, and office buildings therefore require alternative sensing technologies for localization and environmental perception.

Several sensing modalities have been explored over the years, including:

- Cameras
- LiDAR
- Radar
- WiFi

Among these, commodity WiFi hardware is particularly attractive because it is already deployed in most indoor environments. Rather than requiring dedicated sensing hardware, WiFi sensing attempts to extract information about the surrounding environment directly from wireless communication signals.

Unlike Received Signal Strength Indicator (RSSI), modern IEEE 802.11n/ac devices expose **Channel State Information (CSI)**, which contains complex-valued measurements of every OFDM subcarrier. CSI preserves both the amplitude and phase response of the wireless channel, making it possible to estimate much richer environmental information than simple received power.

Throughout this project we investigate how different research directions exploit CSI:

- SpotFi extracts geometric information.
- Widar extracts motion information.
- DeepFi learns robust CSI representations.
- Our final objective is to combine these complementary approaches into a unified perception framework for autonomous drone navigation.

Rather than reproducing papers independently, this notebook follows the complete research journey from raw CSI measurements to a proposed multi-modal sensing architecture.

---

# 2. Motivation

During our literature review we observed that different CSI-based systems recover different aspects of the wireless environment.

For example,

SpotFi estimates

- Angle of Arrival (AoA)
- Time of Flight (ToF)

which describe the geometry of propagation paths.

Widar estimates

- Doppler frequency
- Velocity spectrum
- Micro-Doppler signatures

which describe moving objects inside the environment.

DeepFi approaches the problem differently by learning latent representations of CSI through deep neural networks instead of explicitly modeling propagation physics.

Each approach successfully extracts one aspect of the environment while discarding others.

This naturally raises an important question:

> Can the complementary information extracted by these systems be fused into a single perception pipeline capable of localization, mapping, dynamic object detection, and autonomous navigation?

Answering this question forms the central motivation of this project.

---

# 3. Problem Statement

Current WiFi sensing systems are generally designed for a single downstream task.

Examples include

- Indoor localization
- Human activity recognition
- Gesture recognition
- Occupancy estimation

Although these systems achieve impressive performance within their respective domains, they often optimize for one type of information while ignoring others.

For example,

SpotFi focuses on propagation geometry.

Widar focuses on motion.

DeepFi focuses on learned feature representations.

Our objective is not merely to reproduce these systems but to understand:

- what information each method extracts,
- what information each method discards,
- how these methods complement one another,
- and whether their strengths can be combined into a unified architecture suitable for autonomous navigation.

---

# 4. Research Objectives

This notebook follows five primary objectives.

## Objective 1

Understand the mathematical foundations of WiFi CSI.

Topics include

- CSI representation
- OFDM subcarriers
- Multipath propagation
- Complex channel response

---

## Objective 2

Reproduce the Widar 3.0 signal processing pipeline.

Implemented components include

- CSI parsing
- Antenna selection
- Amplitude adjustment
- Conjugate multiplication
- Butterworth filtering
- PCA
- STFT
- Doppler spectrum generation
- Velocity mapping

---

## Objective 3

Understand SpotFi.

Rather than immediately implementing the algorithm, we first study

- AoA estimation
- ToF estimation
- Joint AoA-ToF estimation
- MUSIC algorithm
- Multipath resolution

to understand how geometric information is recovered from CSI.

---

## Objective 4

Understand DeepFi.

Our focus is understanding

- CSI fingerprinting
- Learned latent representations
- Offline training
- Online localization

and how learned features differ from manually engineered signal processing pipelines.

---

## Objective 5

Design a unified CSI perception architecture capable of combining

- geometric information,
- motion information,
- learned CSI representations,
- and inertial measurements

for autonomous indoor drone navigation.

---

# 5. Repository Structure

```text
wifi-csi-research/

README.md

docs/
    WiFi_CSI_Research_Notebook.md

notebooks/

src/

data/

models/

results/
```

---

# 6. Learning Roadmap

The notebook follows the chronological order in which the project was developed.

```
Raw CSI

↓

Understanding CSI

↓

Dataset Exploration

↓

Signal Processing

↓

Widar 3.0

↓

SpotFi

↓

DeepFi

↓

Literature Review

↓

Unified CSI Representation

↓

CSI + IMU Fusion

↓

Indoor Drone Navigation
```

Each chapter builds directly upon the previous one.

---


