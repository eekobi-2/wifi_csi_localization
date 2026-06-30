# Chapter 7 : SpotFi — Recovering Geometry from CSI

> **Question**
>
> After reconstructing the complete Widar 3.0 pipeline, one important question remains.
>
> CSI does not only contain motion information.
>
> Every CSI measurement also contains rich information about
>
> - propagation distance,
> - signal direction,
> - multipath reflections,
> - and wireless geometry.
>
> Can this information be recovered?
>
> SpotFi answers this question by treating CSI not as a motion signal but as a geometric measurement of the wireless channel.

---

# 7.1 Motivation

Throughout the previous chapter, we reconstructed the entire Widar 3.0 pipeline.

```
Raw CSI

↓

Reference Selection

↓

Amplitude Adjustment

↓

Conjugate Multiplication

↓

Filtering

↓

PCA

↓

STFT

↓

Velocity Mapping

↓

CNN-GRU
```

The objective of Widar was

> Recover **motion** from CSI.

SpotFi asks an entirely different question.

> Recover **geometry** from CSI.

Although both algorithms operate on exactly the same CSI measurements, they preserve different physical information.

---

## Motion vs Geometry

Human motion changes the wireless channel over **time**.

Wireless geometry changes the channel over **space**.

Consequently, Widar and SpotFi observe different dimensions of the same signal.

```
                    Same CSI

                        │

        ┌───────────────┴───────────────┐

        ▼                               ▼

      Widar                         SpotFi

 Motion Estimation            Geometry Estimation

 Temporal Variation           Spatial Variation

 Doppler                      AoA + ToF

 Velocity Spectrum            Multipath Geometry
```

This distinction is the foundation of the remainder of this chapter.

---

# 7.2 Philosophy: Widar vs SpotFi

One of the biggest insights obtained during this study was that Widar and SpotFi follow completely different philosophies for handling CSI.

---

## Widar Philosophy

Widar assumes that the absolute CSI phase is unreliable.

Instead of estimating the hardware errors,

it attempts to remove them.

```
Raw CSI

↓

Reference Antenna

↓

Amplitude Adjustment

↓

Conjugate Multiplication

↓

Relative Phase
```

The key assumption is

> Common hardware errors are shared across receive antennas.

Therefore,

computing

\[
H_iH_{ref}^{*}
\]

cancels most of the common phase errors.

This produces an excellent signal for Doppler estimation.

However,

absolute propagation phase is lost.

---

## SpotFi Philosophy

SpotFi cannot discard the absolute phase.

Why?

Because localization depends directly on

- propagation delay,
- propagation direction.

Both quantities are encoded inside the absolute CSI phase.

Instead of cancelling hardware errors,

SpotFi attempts to estimate them.

```
Measured Phase

↓

Model Hardware Errors

↓

Estimate Error Terms

↓

Recover Physical Phase

↓

Estimate Geometry
```

This is a fundamentally different philosophy.

---

# Comparison

| Widar | SpotFi |
|--------|---------|
| Relative Phase | Absolute Phase |
| Hardware cancellation | Hardware estimation |
| Conjugate multiplication | Phase calibration |
| Motion estimation | Geometry estimation |
| Doppler | AoA + ToF |

---

# 7.3 CSI Signal Model

To understand SpotFi,

we first derive the CSI signal model.

Consider a single propagation path.

The received signal can be written as

\[
H(f)
=
Ae^{-j2\pi f\tau}
\]

where

- \(A\) is the complex attenuation,
- \(f\) is the carrier frequency,
- \(\tau\) is the propagation delay.

This equation immediately tells us

> Phase depends on propagation delay.

---

## OFDM Subcarriers

WiFi does not transmit a single carrier.

Instead,

it transmits many OFDM subcarriers.

The frequency of the \(k^{th}\) subcarrier is

\[
f_k
=
f_c
+
k\Delta f
\]

where

- \(f_c\) is the center frequency,
- \(\Delta f\) is the subcarrier spacing.

Substituting into the CSI equation,

\[
H(k)
=
Ae^{-j2\pi(f_c+k\Delta f)\tau}
\]

Taking the phase,

\[
\phi(k)
=
-2\pi f_c\tau
-
2\pi k\Delta f\tau
\]

This equation is extremely important.

---

# 7.4 A Fundamental Observation

Notice that

\[
\phi(k)
=
-2\pi f_c\tau
-
2\pi k\Delta f\tau
\]

has the form

\[
\phi(k)
=
ak+b
\]

where

\[
a
=
-2\pi\Delta f\tau
\]

and

\[
b
=
-2\pi f_c\tau.
\]

This means

> **The phase varies linearly across OFDM subcarriers.**

This linear relationship is not an implementation trick.

It is a direct consequence of the OFDM signal model.

---

# 7.5 Hardware Imperfections

Unfortunately,

the measured CSI phase is not

\[
\phi_{true}.
\]

Commodity WiFi devices introduce several hardware impairments.

The measured phase becomes

\[
\phi_{measured}
=
\phi_{true}
+
\phi_{SFO}
+
\phi_{PDD}
+
\phi_{CFO}
+
\phi_{offset}
+
n
\]

where

- SFO : Sampling Frequency Offset
- PDD : Packet Detection Delay
- CFO : Carrier Frequency Offset
- Offset : Constant packet-dependent phase
- \(n\) : Measurement noise

These errors dominate the measured CSI phase.

Without correction,

AoA and ToF estimation become impossible.

---

# 7.6 Why Line Fitting Works

The crucial insight of SpotFi is that

the dominant hardware errors

introduce an approximately **linear phase distortion** across subcarriers.

Conceptually,

```
Measured Phase

^

|

|          /

|        /

|      /

|    /

|__ /____________________>

      Subcarrier Index
```

The slope originates primarily from

- Sampling Frequency Offset
- Packet Detection Delay

while the intercept corresponds to

the constant phase offset.

Instead of estimating each hardware error independently,

SpotFi simply estimates the best fitting line.

---

# 7.7 Phase Sanitization

For every received packet,

SpotFi performs

\[
\phi(k)
=
ak+b
\]

using linear regression.

The estimated line

\[
ak+b
\]

represents

the hardware-induced distortion.

The corrected phase becomes

\[
\phi_{corrected}
=
\phi_{measured}
-
(ak+b).
\]

This process is known as

**Phase Sanitization**.

---

## Why Is This Better Than Using Channel Indices Directly?

One might wonder

why SpotFi performs a line fit instead of simply subtracting the theoretical phase associated with the subcarrier indices.

The answer is that

the actual hardware errors vary from packet to packet.

Each received packet has

- a different timing offset,
- a different packet detection delay,
- a different constant phase offset.

Consequently,

every packet possesses

its own

best fitting line.

Estimating

the slope

and

intercept

for every packet

adapts automatically to the current hardware state.

This makes the calibration considerably more robust than using a fixed correction.

---

# 7.8 Comparison with Widar

This is perhaps the most important conceptual distinction between the two systems.

### Widar

```
Hardware Errors

↓

Cancel

↓

Relative Phase

↓

Motion
```

### SpotFi

```
Hardware Errors

↓

Estimate

↓

Absolute Phase

↓

Geometry
```

Neither approach is universally superior.

Their objectives are fundamentally different.

---

# 7.9 Information Flow

| Stage | Preserves | Removes |
|---------|------------|-----------|
| Raw CSI | Complete wireless channel | Nothing |
| Phase Sanitization | Physical propagation phase | Hardware phase distortion |
| Remaining Stages | Geometry | Packet-dependent hardware errors |

Unlike Widar,

SpotFi preserves the physical phase because it is the quantity required for localization.

---

# Research Notes

One of the most important realizations during this study was that SpotFi never attempts to estimate every hardware impairment independently.

Instead,

it exploits the observation that the combined effect of the dominant impairments appears as an approximately linear phase trend across the OFDM subcarriers.

This converts a difficult hardware calibration problem into a simple line-fitting problem performed independently for every received packet.

Compared to Widar's conjugate multiplication,

this approach preserves the absolute propagation phase and therefore enables the recovery of geometric information such as Angle of Arrival (AoA) and Time of Flight (ToF).

---

# Looking Ahead

After recovering the physical CSI phase,

the next challenge is determining

- **where the signal came from**, and
- **how far it traveled**.

This requires estimating two fundamental propagation parameters:

- **Angle of Arrival (AoA)**
- **Time of Flight (ToF)**

Unlike Widar,

which analyzes the evolution of CSI over time,

SpotFi analyzes how CSI varies across

- antennas,
- and OFDM subcarriers.

These two dimensions together form the basis of the virtual antenna array and the joint AoA-ToF estimation developed in the next section.

# 7.19 Covariance Matrix

After constructing the virtual antenna array, SpotFi now possesses multiple observations of the same wireless channel.

Instead of processing every CSI packet independently, SpotFi estimates their statistical relationship by constructing the **sample covariance matrix**.

Suppose the measurement matrix is

\[
X=[x_1,x_2,\cdots,x_N]
\]

where each column represents one virtual array observation.

The covariance matrix is computed as

\[
R=\frac{1}{N}XX^{H}
\]

where

- \(N\) is the number of packets,
- \(H\) denotes the Hermitian transpose.

---

## Why Covariance?

Individual CSI packets contain

- thermal noise,
- quantization errors,
- random measurement fluctuations.

Averaging across multiple packets suppresses these random effects while preserving the underlying propagation structure.

Consequently, the covariance matrix captures the correlation introduced by the propagation paths rather than the instantaneous noise.

---

## Comparison with Widar

Although Widar also performs an eigen-decomposition through PCA, the objectives are fundamentally different.

| Widar | SpotFi |
|--------|---------|
| PCA | Covariance Matrix |
| Dimension reduction | Signal subspace estimation |
| Keep dominant component | Separate signal and noise |

The covariance matrix is therefore not a dimensionality reduction step. Instead, it provides the foundation for subspace estimation.

---

# 7.20 Eigenvalue Decomposition

The covariance matrix is decomposed as

\[
R=U\Lambda U^{H}
\]

where

- \(U\) contains the eigenvectors,
- \(\Lambda\) contains the corresponding eigenvalues.

The eigenvalues naturally divide into two groups.

```
Large Eigenvalues
        │
        ▼
 Signal Subspace

Small Eigenvalues
        │
        ▼
 Noise Subspace
```

If there are \(L\) propagation paths,

the first \(L\) eigenvectors span the signal subspace,

while the remaining eigenvectors span the noise subspace.

This separation is the key idea behind the MUSIC algorithm.

---

# 7.21 The 2D MUSIC Algorithm

At this point, SpotFi has

- a calibrated CSI measurement,
- a virtual antenna array,
- and the signal/noise subspaces.

The remaining question is

> **Which Angle of Arrival and Time of Flight best explain the measured CSI?**

Instead of solving this directly,

SpotFi evaluates every possible pair

\[
(\theta,\tau).
\]

---

## Orthogonality Principle

Suppose a candidate steering vector is

\[
a(\theta,\tau).
\]

If this candidate corresponds to a true propagation path,

then it lies entirely inside the signal subspace.

Consequently,

it becomes orthogonal to the noise subspace.

Mathematically,

\[
a^{H}E_n\approx0
\]

where

- \(E_n\) is the matrix containing the noise eigenvectors.

This simple observation forms the basis of MUSIC.

---

## MUSIC Pseudo-Spectrum

The likelihood of a propagation path is computed using

\[
P(\theta,\tau)=
\frac{1}
{a^{H}(\theta,\tau)
E_nE_n^{H}
a(\theta,\tau)}
\]

where

- \(a(\theta,\tau)\) is the joint AoA-ToF steering vector,
- \(E_n\) is the noise subspace.

If the steering vector aligns with a true signal,

the denominator approaches zero,

causing the pseudo-spectrum to exhibit a sharp peak.

---

## Two-Dimensional Search

Unlike conventional MUSIC,

SpotFi searches over both

- Angle of Arrival,
- Time of Flight.

Conceptually,

```
            ToF

              ↑

              │

              │        ▲

              │      ▲

              │   ▲

──────────────┼────────────────→ AoA

            Peak
```

Every point in this heatmap represents one possible propagation path.

The brighter the peak,

the more likely that a signal arrived with the corresponding angle and propagation delay.

---

## Why 2D MUSIC?

Estimating AoA alone cannot separate paths having identical arrival angles.

Estimating ToF alone cannot separate paths having identical delays.

By jointly estimating both parameters,

SpotFi significantly improves multipath resolution while using only commodity WiFi hardware.

This joint estimation is one of the principal contributions of the paper.

---

# 7.22 Peak Detection

The output of the MUSIC algorithm is a two-dimensional pseudo-spectrum.

SpotFi identifies the local maxima within this spectrum.

Each peak corresponds to one candidate propagation path.

```
Peak 1
↓

Line-of-Sight

Peak 2
↓

Wall Reflection

Peak 3
↓

Furniture Reflection
```

The direct path is then selected using additional heuristics based on

- propagation delay,
- signal strength,
- geometric consistency.

Once the direct path has been identified,

its

- Angle of Arrival,
- Time of Flight

can be used to estimate the user's location.

---

# 7.23 Complete SpotFi Pipeline

The complete SpotFi localization pipeline can now be summarized as

```
                         Raw CSI
                            │
                            ▼
                    CSI Parsing
                            │
                            ▼
                  Phase Sanitization
                            │
                            ▼
                Virtual Antenna Array
                            │
                            ▼
            Joint AoA-ToF Steering Vector
                            │
                            ▼
                  Covariance Matrix
                            │
                            ▼
              Eigenvalue Decomposition
                            │
                            ▼
          Signal / Noise Subspaces
                            │
                            ▼
                  2D MUSIC Search
                            │
                            ▼
                 Peak Detection
                            │
                            ▼
              Direct Path Selection
                            │
                            ▼
                    User Localization
```

Unlike Widar,

which gradually transforms CSI into a motion representation,

SpotFi preserves the propagation geometry throughout the entire pipeline.

---

# 7.24 SpotFi vs Widar

Although both systems begin with identical CSI measurements, they extract fundamentally different physical representations.

| Property | Widar | SpotFi |
|----------|--------|---------|
| Objective | Gesture Recognition | Indoor Localization |
| Physical Quantity | Doppler | AoA + ToF |
| Information Source | Temporal Variation | Spatial & Frequency Variation |
| Hardware Correction | Conjugate Multiplication | Phase Sanitization |
| Representation | Velocity Spectrum | Multipath Geometry |
| Signal Processing | Filtering + PCA + STFT | Covariance + MUSIC |
| Optimization | Velocity Mapping | Subspace Search |
| Neural Network | CNN-GRU | None |
| Output | Motion | Position |

Neither approach is universally superior.

Rather,

they extract complementary information from the same wireless channel.

---

# 7.25 Research Notes

Several important observations emerged while studying SpotFi.

- Unlike Widar, SpotFi never transforms the CSI into another signal representation such as Doppler. Instead, it preserves the physical interpretation of the wireless channel throughout the pipeline.

- The key innovation is not merely the MUSIC algorithm, but the realization that the OFDM subcarriers can be combined with the receive antennas to construct a virtual antenna array.

- The use of **joint AoA-ToF estimation** significantly improves multipath resolution compared to estimating either parameter independently.

- SpotFi is a purely physics-based localization algorithm. Every stage—from phase sanitization to subspace decomposition—is derived from electromagnetic propagation and array signal processing rather than machine learning.

---

# 7.26 Beyond the Paper

While SpotFi remains one of the most elegant CSI-based localization systems, several opportunities for improvement exist.

1. Replace handcrafted phase sanitization with a learnable calibration network.

2. Replace the exhaustive 2D MUSIC search with a differentiable neural estimator.

3. Jointly estimate AoA, ToF, and Doppler to recover both geometry and motion.

4. Fuse SpotFi's geometric representation with Widar's velocity representation instead of treating them as independent pipelines.

5. Incorporate IMU measurements to improve localization robustness during rapid platform motion, making the approach suitable for autonomous robots and drones.

---

# Transition to DeepFi

At this point we have studied two fundamentally different interpretations of CSI.

```
                    Raw CSI
                        │
        ┌───────────────┴───────────────┐
        ▼                               ▼
      Widar                         SpotFi

 Motion                      Geometry

 Doppler                     AoA + ToF

 Velocity                    Multipath
```

Both methods rely heavily on handcrafted signal processing and physical models.

The next chapter takes a completely different perspective.

Instead of explicitly deriving motion or geometry from CSI, **DeepFi** learns a latent representation directly from the wireless channel using deep neural networks.

This marks the transition from **physics-driven feature engineering** to **data-driven representation learning**, completing the three major paradigms of CSI-based indoor sensing explored in this notebook.
