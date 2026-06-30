# Chapter 9 : Literature Review and State of the Art

> **Question**
>
> After studying Widar, SpotFi, and DeepFi individually, what does the broader Wi-Fi sensing landscape look like?
>
> More importantly,
>
> where is current research heading, and what challenges remain unsolved?

---

# 9.1 Evolution of Wi-Fi Sensing

Over the past decade, Wi-Fi sensing has evolved from simple signal-strength based localization into a rich sensing modality capable of estimating

- human motion,
- indoor position,
- gesture recognition,
- activity recognition,
- respiration,
- occupancy,
- and environmental geometry.

The driving factor behind this evolution has been the transition from **Received Signal Strength (RSS)** measurements to **Channel State Information (CSI)**.

```
RSS

↓

CSI

↓

Physics-based CSI

↓

Learning-based CSI

↓

Multi-modal Perception
```

This evolution reflects an increasing ability to exploit the fine-grained information contained within the wireless channel.

---

# 9.2 The Ma et al. Survey (ACM Computing Surveys, 2019)

One of the most influential review papers in Wi-Fi sensing is

> **The Ma et al. Survey (ACM Computing Surveys, 2019)**

Rather than proposing a new algorithm, the survey provides a comprehensive taxonomy of CSI-based sensing systems and identifies the major research directions up to 2019.

---

## Taxonomy of Wi-Fi Sensing

The survey categorizes CSI applications into several broad areas.

```
Wi-Fi Sensing

│

├── Indoor Localization

├── Gesture Recognition

├── Human Activity Recognition

├── Tracking

├── Health Monitoring

├── Occupancy Detection

├── Through-wall Sensing

└── Smart Environments
```

Although these applications appear different,

they all exploit changes in the wireless propagation channel.

---

## Indoor Localization Methods

For localization, the survey broadly classifies existing systems into four categories.

### RSS-based Localization

```
RSS

↓

Fingerprint

↓

Position
```

Advantages

- Simple implementation
- Low computational cost

Limitations

- Poor spatial resolution
- Sensitive to environmental changes
- Limited localization accuracy

---

### CSI Fingerprinting

```
CSI

↓

Fingerprint Database

↓

Matching

↓

Position
```

Representative systems

- DeepFi
- FIFS
- ConFi

Advantages

- Rich channel information
- Higher localization accuracy

Limitations

- Requires offline training
- Environment dependent

---

### Model-based Localization

```
CSI

↓

AoA

↓

ToF

↓

Geometry

↓

Localization
```

Representative systems

- SpotFi
- Chronos
- Phaser

Advantages

- Physically interpretable
- No large fingerprint database

Limitations

- Sensitive to calibration
- Higher computational complexity

---

### Doppler-based Systems

```
CSI

↓

Doppler

↓

Motion

↓

Activity
```

Representative systems

- WiDance
- Widar

Although primarily designed for activity recognition,

these systems demonstrate that CSI can also capture dynamic motion information.

---

## Key Observations from the Survey

The survey highlights several common challenges.

- Hardware variability
- Multipath propagation
- Environmental dynamics
- Scalability
- Real-time processing
- Generalization across environments

Perhaps the most important conclusion is that **no single CSI representation is sufficient for all sensing tasks**.

Different applications require different representations of the wireless channel.

This observation strongly supports the complementary nature of Widar, SpotFi, and DeepFi.

---

# 9.3 Wi-Drone: Wi-Fi-based 6-DoF Tracking for Indoor Drone Flight Control

The next major step in CSI research is moving beyond localization toward autonomous robotics.

One example is

> **Wi-Drone: Wi-Fi-based 6-DoF Tracking for Indoor Drone Flight Control**

Unlike conventional localization systems,

Wi-Drone estimates the complete pose of a flying drone.

---

## Six Degrees of Freedom

```
Translation

x

y

z

+

Rotation

Roll

Pitch

Yaw
```

Rather than estimating only the drone's position,

the system continuously tracks its full motion state.

---

## Core Pipeline

The overall processing pipeline can be summarized as

```
Wi-Fi CSI

↓

CSI Calibration

↓

Motion / Pose Estimation

↓

Flight Controller

↓

Drone Navigation
```

Unlike SpotFi,

which estimates a static location,

Wi-Drone performs **continuous pose tracking**, making it suitable for closed-loop control.

---

## Key Technical Ideas

The system exploits the fact that drone motion continuously changes the wireless channel.

Changes in CSI encode information about

- translation,
- orientation,
- multipath evolution.

By analyzing these temporal changes, the system estimates the drone's six-degree-of-freedom state in real time.

This represents a transition from **localization** to **navigation**.

---

## Why It Is Important

Wi-Drone demonstrates an important shift in the field.

Earlier systems focused on estimating

```
Where is the user?
```

Modern systems instead ask

```
How should the robot move?
```

CSI is no longer used only for sensing.

It becomes part of the perception loop for autonomous navigation.

---

# 9.4 Current State of the Art

Reviewing recent CSI literature reveals several consistent trends.

---

## Trend 1 : From Handcrafted Features to Learned Representations

Early systems relied on manually designed features such as

- RSS
- AoA
- ToF
- Doppler

Modern systems increasingly employ

- deep neural networks,
- self-supervised learning,
- transformer architectures.

Representation learning has become the dominant paradigm.

---

## Trend 2 : From Single-Modality to Sensor Fusion

Recent research increasingly combines CSI with complementary sensors.

Examples include

```
Wi-Fi + IMU

Wi-Fi + Camera

Wi-Fi + LiDAR

Wi-Fi + UWB
```

Each sensor compensates for the weaknesses of the others.

Sensor fusion has therefore become a major research direction.

---

## Trend 3 : From Localization to SLAM

The objective is no longer simply estimating position.

Modern systems seek to recover

- trajectory,
- environmental structure,
- dynamic obstacles,
- semantic understanding.

This moves Wi-Fi sensing closer to simultaneous localization and mapping (SLAM).

---

## Trend 4 : From Human-Centered Sensing to Robotics

The focus is gradually shifting from

- gesture recognition,
- occupancy sensing,

toward

- autonomous robots,
- mobile platforms,
- drones,
- warehouse automation.

CSI is increasingly viewed as an additional perception sensor rather than a standalone localization tool.

---

# 9.5 Summary of Existing Approaches

The systems studied throughout this notebook can be summarized as follows.

| Method | Primary Representation | Strength | Limitation |
|---------|------------------------|----------|------------|
| Widar | Doppler / Velocity | Motion understanding | Limited geometric information |
| SpotFi | AoA + ToF | High localization accuracy | Sensitive to calibration |
| DeepFi | Learned embeddings | Automatic feature learning | Requires extensive training |
| Wi-Drone | 6-DoF pose | Navigation and control | Focused on drone pose estimation |

Each method captures only one aspect of the wireless channel.

---

# 9.6 Research Gap

Despite the significant progress in CSI sensing, several limitations remain.

## Observation 1

SpotFi preserves **geometry**.

---

## Observation 2

Widar preserves **motion**.

---

## Observation 3

DeepFi preserves **statistical representations**.

---

## Observation 4

Modern robotic systems increasingly rely on **sensor fusion**, particularly IMUs, to improve robustness.

---

## Observation 5

Current CSI systems are typically optimized for a single downstream task, such as localization or gesture recognition.

Few systems attempt to preserve **geometry**, **motion**, and **learned channel representations** simultaneously.

---

# Motivation for This Work

The literature reviewed in this notebook suggests that these approaches should not be viewed as competing alternatives.

Instead,

they provide complementary views of the same wireless channel.

```
                    Raw CSI
                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
    SpotFi           Widar          DeepFi
   Geometry         Motion      Representation
   AoA + ToF        Doppler      Latent Features
        │               │                │
        └───────────────┼────────────────┘
                        ▼
          Unified CSI Representation
                        │
                 IMU Integration
                        │
              Multi-modal Fusion
                        │
          Localization • Mapping • Navigation
```

This observation motivates the architecture proposed in the following chapter, where geometry, motion, learned CSI representations, and inertial measurements are integrated into a unified perception framework for autonomous indoor drone navigation.