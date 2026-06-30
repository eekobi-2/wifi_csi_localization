# Chapter 8 : DeepFi — Learning CSI Representations

> **Question**
>
> After studying Widar and SpotFi, a natural question arises.
>
> Both systems rely heavily on handcrafted signal processing and physical models.
>
> Can a neural network learn a useful representation of the wireless channel directly from CSI without explicitly estimating Doppler, Angle of Arrival, or Time of Flight?
>
> DeepFi attempts to answer this question.

---

# 8.1 Motivation

The previous chapters demonstrated two fundamentally different ways of interpreting CSI.

Widar transformed CSI into a **motion representation**.

```
Raw CSI

↓

Signal Processing

↓

Doppler

↓

Velocity

↓

Gesture
```

SpotFi transformed CSI into a **geometric representation**.

```
Raw CSI

↓

Phase Calibration

↓

AoA

↓

ToF

↓

Localization
```

Although both approaches are highly interpretable,

they require

- handcrafted preprocessing,
- physical modeling,
- expert knowledge of wireless propagation.

This naturally raises an important question.

> **Can the wireless channel itself become the feature?**

DeepFi answers this question by replacing handcrafted feature engineering with representation learning.

---

# 8.2 A Shift in Philosophy

DeepFi does not attempt to estimate any explicit physical quantity.

It does **not** compute

- Doppler,
- Velocity,
- Angle of Arrival,
- Time of Flight.

Instead,

it attempts to learn a compact representation directly from CSI.

```
Raw CSI

↓

Neural Network

↓

Latent Representation

↓

Localization
```

The philosophy is fundamentally different.

Instead of asking

> Which physical quantity should we estimate?

DeepFi asks

> Which representation best describes this wireless channel?

---

# 8.3 Three Views of CSI

By this point,

three different interpretations of CSI have emerged.

```
                    Raw CSI

                        │

        ┌───────────────┼───────────────┐

        ▼               ▼               ▼

      Widar         SpotFi          DeepFi

      Motion       Geometry     Representation

      Doppler      AoA + ToF     Latent Features

      Physics      Physics      Deep Learning
```

Each method observes exactly the same CSI measurements,

yet preserves different information.

| Method | Learns | Representation |
|----------|------------|----------------|
| Widar | Motion | Velocity Spectrum |
| SpotFi | Geometry | AoA + ToF |
| DeepFi | Statistical Structure | Latent Embedding |

This observation will later motivate our proposed fusion architecture.

---

# 8.4 Why Fingerprinting?

Indoor localization can be formulated as a fingerprinting problem.

Suppose we stand at a fixed position.

The transmitted WiFi signal experiences

- reflections,
- scattering,
- diffraction,
- attenuation.

These propagation effects depend on

- room geometry,
- furniture,
- walls,
- nearby objects.

Consequently,

every location produces a unique wireless channel.

```
Position

↓

Propagation Environment

↓

Multipath

↓

CSI

↓

Wireless Fingerprint
```

Rather than estimating geometry explicitly,

DeepFi treats this fingerprint as the quantity to be learned.

---

# 8.5 Why Not RSS?

Earlier indoor localization systems primarily relied on

Received Signal Strength (RSS).

However,

RSS contains only a single scalar value per packet.

```
RSS

↓

-52 dBm
```

This is insufficient for accurately distinguishing nearby locations.

CSI provides significantly richer information.

Each packet contains

- multiple antennas,
- multiple OFDM subcarriers,
- complex amplitudes,
- complex phases.

```
CSI

↓

30 Complex Subcarriers

↓

Rich Multipath Information
```

The higher dimensionality makes CSI a much stronger fingerprint.

---

# RSS vs CSI

| RSS | CSI |
|------|------|
| Single scalar | Multiple complex measurements |
| Low dimensional | High dimensional |
| Sensitive to fading | Rich multipath information |
| Weak fingerprint | Strong fingerprint |

This richer representation forms the foundation of DeepFi.

---

# 8.6 Why Deep Learning?

Although CSI provides a powerful fingerprint,

it is also highly complex.

Consider one CSI packet.

```
Packet

↓

3 Receive Antennas

↓

30 Subcarriers

↓

90 Complex Values
```

The relationship between these values and the physical location is

highly nonlinear.

Designing handcrafted features becomes increasingly difficult.

Instead,

DeepFi attempts to learn this nonlinear mapping automatically.

---

# 8.7 Representation Learning

Representation learning attempts to transform high-dimensional observations into a compact feature space.

```
High-Dimensional CSI

↓

Compression

↓

Latent Representation

↓

Localization
```

The learned representation should preserve

the information necessary for localization

while discarding redundant variations.

Unlike Widar and SpotFi,

the representation has

no explicit physical interpretation.

It is discovered entirely from data.

---

# 8.8 Relation to PCA

Earlier,

while studying Widar,

we encountered

Principal Component Analysis (PCA).

```
60 CSI Streams

↓

PCA

↓

1 Principal Component
```

PCA performs

**linear dimensionality reduction.**

DeepFi extends this idea.

Instead of learning

a linear projection,

it learns

a nonlinear representation.

```
PCA

↓

Linear Compression

↓

One Projection


Autoencoder

↓

Nonlinear Compression

↓

Learned Representation
```

This transition from linear to nonlinear feature learning is one of the major conceptual contributions of DeepFi.

---

# Research Notes

Studying DeepFi immediately reveals a philosophical departure from both Widar and SpotFi.

Rather than explicitly modeling wireless propagation,

DeepFi assumes that the neural network can discover useful representations directly from the CSI measurements.

This does not eliminate the underlying physics.

Instead,

the physical relationships become implicitly encoded within the learned feature space rather than being explicitly derived through signal processing.

---

# Looking Ahead

Having established why CSI can be viewed as a high-dimensional fingerprint,

the next question becomes

> **How should a neural network learn this fingerprint?**

DeepFi answers this using a **deep autoencoder**, trained to compress and reconstruct CSI while preserving the latent structure required for localization.

Unlike conventional classifiers,

the autoencoder is not trained to predict positions directly.

Instead,

it first learns an efficient representation of the wireless channel itself.

This learned representation becomes the basis for the localization stage described in the next section.

# 8.9 Deep Autoencoder

The central contribution of DeepFi is the use of a **deep autoencoder** to learn a compact representation of CSI.

Unlike a conventional neural network trained for classification,

an autoencoder attempts to reconstruct its own input.

```
                 Input CSI
                     │
                     ▼
              Encoder Network
                     │
                     ▼
              Latent Representation
                     │
                     ▼
              Decoder Network
                     │
                     ▼
            Reconstructed CSI
```

During training,

the network minimizes the reconstruction error

\[
L=\|X-\hat{X}\|_2^2
\]

where

- \(X\) is the original CSI,
- \(\hat{X}\) is the reconstructed CSI.

The bottleneck layer forces the network to compress the high-dimensional CSI into a lower-dimensional latent representation while preserving the essential characteristics of the wireless channel.

---

# 8.10 Offline Training

DeepFi operates in two distinct phases.

## Phase 1 : Offline Training

CSI packets are collected at known reference locations.

```
Reference Point

↓

Collect CSI

↓

Train Autoencoder

↓

Store Network Parameters
```

Unlike traditional fingerprint databases that store raw CSI,

DeepFi stores the learned neural network parameters associated with each location.

These parameters capture the statistical characteristics of the wireless channel.

---

# 8.11 Online Localization

During deployment,

the current CSI measurement is passed through the trained network.

```
New CSI

↓

Forward Pass

↓

Compare with Stored Models

↓

Estimate Location
```

The estimated position corresponds to the reference location whose trained model best reconstructs the observed CSI.

Unlike Widar,

no Doppler computation is required.

Unlike SpotFi,

no AoA or ToF estimation is required.

Localization is performed directly in the learned feature space.

---

# 8.12 Why an Autoencoder?

An autoencoder offers several advantages over handcrafted feature engineering.

- Learns nonlinear relationships between CSI measurements.
- Automatically extracts compact representations.
- Does not require explicit propagation models.
- Can model complex multipath environments.

Compared to PCA,

the autoencoder performs nonlinear dimensionality reduction.

| PCA | Autoencoder |
|------|-------------|
| Linear projection | Nonlinear projection |
| Closed-form solution | Gradient-based learning |
| Fixed basis | Data-dependent basis |
| Limited expressiveness | Learns complex channel structure |

---

# 8.13 DeepFi Pipeline

The complete DeepFi pipeline can be summarized as

```
                     Raw CSI
                        │
                        ▼
                CSI Preprocessing
                        │
                        ▼
               Deep Autoencoder
                        │
                        ▼
             Latent Representation
                        │
                        ▼
          Fingerprint Database
                        │
                        ▼
             Similarity Matching
                        │
                        ▼
                 User Location
```

Unlike SpotFi,

the intermediate representation has no explicit physical interpretation.

Instead,

the neural network discovers the representation directly from data.

---

# 8.14 DeepFi vs SpotFi vs Widar

The three systems represent three different philosophies for exploiting CSI.

| Property | Widar | SpotFi | DeepFi |
|----------|--------|---------|---------|
| Goal | Motion Recognition | Localization | Localization |
| Core Idea | Doppler Analysis | AoA + ToF Estimation | Representation Learning |
| Feature Engineering | Heavy | Heavy | Minimal |
| Physical Model | Doppler Physics | Array Signal Processing | Implicit |
| Neural Network | CNN-GRU | None | Autoencoder |
| Intermediate Representation | Velocity Spectrum | Multipath Geometry | Latent Embedding |
| Interpretability | High | High | Low |
| Data Requirement | Moderate | Low | High |

The evolution is evident.

- **Widar** engineers a motion representation.
- **SpotFi** engineers a geometric representation.
- **DeepFi** learns the representation directly from data.

---

# 8.15 Limitations of DeepFi

Although DeepFi eliminates much of the handcrafted signal processing,

it introduces new challenges.

- Requires extensive offline data collection.
- Performance depends heavily on the training environment.
- Limited interpretability compared to physics-based methods.
- Retraining may be required when the environment changes significantly.

Consequently,

DeepFi trades physical interpretability for greater modeling flexibility.

---

# Research Notes

DeepFi marks the transition from **physics-driven feature engineering** to **data-driven representation learning**.

Rather than explicitly estimating Doppler, AoA, or ToF, the network learns a compact embedding of the wireless channel that is optimized for localization.

This idea has influenced many subsequent CSI-based localization systems, where deep neural networks replace handcrafted signal processing while retaining CSI as the primary sensing modality.

---

# Connection to Our Proposed Architecture

Studying Widar, SpotFi, and DeepFi reveals that each method preserves a different aspect of the wireless channel.

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
               IMU Preintegration
                        │
          Cross-modal Transformer
                        │
      Localization • Mapping • Navigation
```

Rather than replacing one approach with another,

our proposed architecture aims to combine

- SpotFi's geometric understanding,
- Widar's motion representation,
- and DeepFi's learned embeddings,

to preserve complementary information that would otherwise be discarded by individual pipelines.