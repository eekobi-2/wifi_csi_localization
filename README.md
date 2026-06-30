# WiFi CSI and Indoor Drone Navigation

> **Goal:** Explore whether WiFi Channel State Information (CSI) can be
> used for indoor localization and ultimately for autonomous drone
> navigation in GPS-denied environments.

------------------------------------------------------------------------

# Overview

This repository documents my exploration of WiFi CSI, beginning from the
fundamentals of wireless propagation and OFDM, progressing through CSI
extraction and processing, and finally studying state-of-the-art
localization systems such as **SpotFi**, **DeepFi**, and the **WiFi
Sensing Survey by Ma et al.**

Rather than simply summarizing papers, the objective was to understand:

-   what information CSI actually contains,
-   how different localization methods exploit that information,
-   why they work,
-   where their assumptions break,
-   and what changes when the CSI receiver itself is mounted on a moving
    drone.

The repository also includes a small practical experiment using the
**Widar 3.0** public dataset to understand how CSI behaves in practice
and why existing datasets are insufficient for UAV-based CSI
localization.

> **Detailed mathematical derivations, signal-processing pipeline,
> literature review, and proposed CSI--IMU architecture are available in
> the `docs/` folder.** The README intentionally focuses on the
> intuition, comparisons, and overall conclusions.

------------------------------------------------------------------------

# Part 1 --- What I Read, What Makes Sense, and Where It Breaks for a Moving Drone

## The basic idea

Unlike RSSI, which reports only received signal strength, **WiFi CSI**
measures the complex channel response for every OFDM subcarrier and
antenna pair. Each CSI measurement contains amplitude and phase
information that captures how electromagnetic waves propagated through
the environment.

Since indoor environments contain rich multipath propagation, every
wall, ceiling, object and person modifies CSI slightly differently.
Consequently, CSI can be viewed as a rich signature of the surrounding
environment rather than simply a communication metric.

Different localization systems exploit different parts of this
information.

------------------------------------------------------------------------

## SpotFi --- Geometry-based localization

SpotFi approaches localization from a physics perspective.

Instead of learning fingerprints, it estimates physical quantities such
as:

-   Angle of Arrival (AoA)
-   Time of Flight (ToF)

using CSI collected from commodity WiFi hardware.

Once AoA and ToF are estimated, multiple access points can triangulate
the transmitter location.

### Why it makes sense

The biggest advantage of SpotFi is interpretability.

Instead of a black-box model saying *"this looks like location X"*,
SpotFi estimates measurable physical parameters describing how radio
waves travelled.

### Major achievements

-   Commodity WiFi localization
-   Around 40 cm median localization accuracy
-   No large fingerprint database required

### Limitations

SpotFi assumes that the direct propagation path can be reliably
separated from reflected paths. In cluttered indoor environments, strong
multipath and phase errors make this difficult. It also assumes
relatively stable hardware calibration and mostly static infrastructure.

------------------------------------------------------------------------

## DeepFi --- Learning-based localization

DeepFi takes a completely different approach.

Instead of estimating geometry, it treats CSI as a location fingerprint
and learns deep representations for each reference location.

Localization becomes a machine learning problem rather than a
signal-processing problem.

### Why it makes sense

Deep neural networks can automatically learn complex CSI patterns that
would be extremely difficult to model analytically.

### Major achievements

-   Demonstrated that CSI fingerprints outperform RSS-based
    fingerprinting.
-   Reduced dependence on explicit wireless propagation models.
-   Showed deep learning can effectively exploit CSI.

### Limitations

DeepFi depends heavily on:

-   large calibration datasets,
-   environment-specific training,
-   static environments,
-   expensive retraining whenever the environment changes.

------------------------------------------------------------------------

## WiFi Sensing Survey (Ma et al.)

The survey was useful because it places almost every CSI application
into a common framework.

It broadly categorizes CSI applications into

-   fingerprinting,
-   geometric localization,
-   Doppler-based sensing,
-   gesture recognition,
-   activity recognition,
-   respiration monitoring,
-   imaging.

The biggest takeaway is that all of these methods use the same raw CSI
measurements but extract different information depending on the
application.

------------------------------------------------------------------------

## Comparing the major approaches

  ----------------------------------------------------------------------------------------
  Method    Core idea       Advantages        Major achievements    Limitations
  --------- --------------- ----------------- --------------------- ----------------------
  SpotFi    Estimate AoA    Physically        \~40 cm localization  Sensitive to phase
            and ToF from    interpretable, no with commodity WiFi   errors, multipath and
            CSI for         fingerprint                             calibration
            geometric       database                                
            localization                                            

  DeepFi    Learn CSI       Learns complex    Better than RSS       Requires extensive
            fingerprints    channel           fingerprinting        training and
            using deep      characteristics                         environment-specific
            learning        automatically                           calibration

  WiFi      Comprehensive   Shows strengths   Unified understanding Highlights unresolved
  Sensing   overview of CSI and weaknesses    of CSI sensing        challenges such as
  Survey    sensing methods across the field                        robustness and
                                                                    generalization
  ----------------------------------------------------------------------------------------

------------------------------------------------------------------------

## My takeaway

After reading these papers, I think no single representation of CSI is
sufficient.

-   SpotFi extracts geometry.
-   DeepFi extracts fingerprints.
-   Doppler-based systems extract motion.
-   Recent systems increasingly combine multiple cues.

The future likely lies in combining these representations instead of
relying on only one.

------------------------------------------------------------------------

## Where everything breaks for a moving drone

Almost every CSI localization paper assumes the receiver is stationary.

A drone violates nearly all of these assumptions.

The biggest challenges are:

1.  **Self-motion contaminates CSI.** The measured channel changes
    because both the environment and the drone move simultaneously.

2.  **Continuous orientation changes.** Roll, pitch and yaw continuously
    alter antenna orientation relative to access points.

3.  **Mechanical vibration.** Airframe vibration introduces phase
    instability that resembles channel variation.

4.  **Rotor-induced Doppler.** Propellers create additional Doppler
    components that overlap with the Doppler signatures used for
    sensing.

5.  **Dynamic multipath.** Every movement changes reflection geometry,
    making fingerprints unstable.

6.  **3D localization.** Most public datasets and algorithms assume 2D
    motion, whereas drones move in full 3D space.

Overall, extending CSI localization from static devices to drones is not
simply applying existing algorithms to a faster platform---it becomes a
fundamentally different sensing problem.

------------------------------------------------------------------------

# Part 2 --- Practical Experiment

## Dataset

I used the **Widar 3.0** public dataset.

Rather than focusing on achieving high accuracy, the objective was to
understand how CSI-derived features behave in practice and what
information they preserve.

------------------------------------------------------------------------

## What I implemented

The Python pipeline

-   loads Widar samples,
-   extracts simple statistical features,
-   trains a Random Forest classifier,
-   predicts room/location labels,
-   evaluates accuracy and feature importance.

The implementation intentionally uses simple handcrafted features
instead of deep neural networks to make the behavior easier to
interpret.

------------------------------------------------------------------------

## What I observed

The classifier performs better than random guessing but is far from
reliable.

The experiment reinforced several observations:

-   preprocessing is extremely important,
-   CSI is highly noisy,
-   feature engineering strongly affects performance,
-   location information exists but is difficult to isolate.

Most importantly, Widar's Body-coordinate Velocity Profile (BVP) was
designed to reduce location-dependence for gesture recognition, making
it an imperfect feature for localization.

------------------------------------------------------------------------

## What changes if the receiver is a drone?

The Widar dataset assumes static WiFi infrastructure and static
receivers.

If the receiver is mounted on a drone, several additional challenges
appear.

### Continuous motion

The receiver continuously changes position while collecting CSI.

### Orientation changes

The antenna pattern rotates due to roll, pitch and yaw.

### Mechanical vibration

Small antenna displacements introduce phase noise that existing
preprocessing pipelines do not explicitly model.

### Rotor-induced Doppler

Propellers generate Doppler components that overlap with genuine
environmental motion.

### Synchronization

Reliable localization now requires accurate synchronization between

-   CSI,
-   IMU,
-   flight controller,
-   and possibly camera measurements.

### Dynamic fingerprints

Fingerprints become time-varying because the sensing platform itself is
moving.

Traditional fingerprint databases therefore become much less reliable.

------------------------------------------------------------------------

# Overall Conclusion

This exploration convinced me that WiFi CSI is an extremely rich sensing
modality.

Current localization systems already demonstrate impressive accuracy for
static receivers, but their assumptions do not transfer directly to
autonomous drones.

A practical CSI-based indoor drone navigation system will likely
require:

-   CSI geometry (AoA/ToF),
-   learned CSI representations,
-   Doppler analysis,
-   IMU fusion,
-   probabilistic state estimation,
-   real-time adaptation to platform dynamics.

Rather than treating CSI purely as a communication measurement or purely
as a fingerprint, I think it should become one component of a larger
multi-sensor perception system.

------------------------------------------------------------------------

# Repository Structure

``` text
README.md
docs/
code/
model_results/
```

The **`docs/`** directory contains detailed explanations of:

-   Wireless propagation fundamentals
-   OFDM and CSI derivation
-   CSI processing pipeline
-   SpotFi
-   DeepFi
-   Literature review
-   CSI--IMU drone architecture
-   Open research challenges
-   Future directions
