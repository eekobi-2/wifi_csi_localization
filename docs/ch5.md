# Chapter 5 : What Information Does CSI Actually Contain?

> **Question**
>
> We now understand what CSI is. But what physical information is actually encoded inside these complex measurements?

---

# 5.1 Motivation

Every CSI measurement is simply a complex number

$$
H = Ae^{j\phi}.
$$

At first glance, this appears to contain only two quantities:

- amplitude
- phase

Yet modern WiFi sensing systems can estimate

- position,
- walking direction,
- body velocity,
- gestures,
- respiration,
- occupancy,
- Angle of Arrival (AoA),
- Time of Flight (ToF),
- Doppler frequency,
- multipath characteristics.

How can so much information be extracted from only amplitude and phase?

The answer is that these quantities are **not measured directly**.

Instead, they are inferred by observing how amplitude and phase vary across different dimensions of the CSI tensor.

---

# 5.2 Revisiting the CSI Tensor

Recall that one packet from the Intel 5300 NIC has dimensions

```
(30, 3, 2)

↓

30 OFDM Subcarriers

3 Receive Antennas

2 Transmit Antennas
```

For an entire recording, the tensor becomes

```
(Number of Packets,
 Subcarriers,
 Rx,
 Tx)

(1445,30,3,2)
```

Each dimension carries different physical information.

---

# 5.3 Information Hidden Across Time

Suppose we observe a single subcarrier over many packets.

```
Packet

1

2

3

4

5

...

↓

Phase

0.10

0.13

0.19

0.31

0.42
```

If nothing moves,

the phase remains almost constant.

If someone walks,

the propagation distance changes,

causing the phase to evolve continuously.

This temporal phase variation gives rise to

- Doppler shift
- Micro-Doppler
- Velocity estimation
- Motion detection

This is exactly the information exploited by **Widar**.

---

# 5.4 Information Hidden Across Antennas

Now fix

- one packet
- one subcarrier

and compare different antennas.

```
Rx1

Rx2

Rx3
```

Each antenna observes the same signal,

but the signal reaches each antenna at a slightly different time.

The resulting phase difference depends on the incoming direction.

```
Wavefront

//////////////

Rx1

Rx2

Rx3
```

This phase difference is the basis for estimating

- Angle of Arrival (AoA).

SpotFi is built almost entirely around this idea.

---

# 5.5 Information Hidden Across Subcarriers

Now fix

- one antenna
- one packet

and examine all 30 subcarriers.

Each subcarrier operates at a slightly different frequency.

Consequently,

each experiences a different phase shift due to propagation delay.

The phase variation across frequency reveals

the signal's propagation time,

known as

**Time of Flight (ToF).**

Unlike AoA,

which depends on antenna spacing,

ToF depends on

frequency diversity.

SpotFi jointly estimates

AoA

and

ToF

to separate multiple propagation paths.

---

# 5.6 Information Hidden Across Transmit Antennas

Although Widar primarily uses a single transmitting antenna,

the Intel 5300 reports CSI for multiple transmit antennas.

These measurements provide

additional spatial diversity,

which can improve

- localization,
- multipath separation,
- beamforming.

For the Widar 3.0 dataset,

this dimension is not heavily exploited,

but it remains available for future work.

---

# 5.7 Information Hidden in Amplitude

Amplitude is often considered less informative than phase,

yet it still reflects

- attenuation,
- shadowing,
- blockage,
- fading,
- path loss.

Large obstacles,

walls,

or people

change the received signal strength.

DeepFi demonstrated that

amplitude patterns alone

contain enough information

to learn

location-specific fingerprints.

---

# 5.8 Information Hidden in Phase

Phase is considerably richer.

Phase changes due to

- propagation delay,
- antenna spacing,
- movement,
- multipath interference,
- oscillator offsets,
- packet synchronization errors.

Unfortunately,

raw phase also contains

hardware-induced distortions,

making calibration essential.

A significant portion of Widar's signal processing pipeline is devoted to recovering physically meaningful phase measurements.

---

# 5.9 The Four Views of CSI

It is useful to think of CSI as four different "views" of the same wireless channel.

```
               CSI
                │
 ┌──────────────┼──────────────┐
 │              │              │
 ▼              ▼              ▼
Time         Antennas     Subcarriers
 │              │              │
 ▼              ▼              ▼
Doppler        AoA           ToF

                │
                ▼
           Multipath
```

Each view emphasizes different physical properties.

No single representation captures everything.

---

# 5.10 Mapping CSI Dimensions to Physical Quantities

| CSI Dimension | Physical Variation | Observable Quantity | Used By |
|---------------|-------------------|---------------------|----------|
| Time | Motion | Doppler | Widar |
| Antennas | Arrival Direction | AoA | SpotFi |
| Subcarriers | Propagation Delay | ToF | SpotFi |
| Amplitude | Path Loss | Fingerprints | DeepFi |
| Phase | Propagation Geometry | All Methods | SpotFi / Widar |

This table summarizes nearly all modern CSI sensing algorithms.

The primary difference between algorithms is not the input data—they all begin with the same CSI tensor—but rather which physical dimension they emphasize during processing.

---

# 5.11 A Unified Perspective

The relationship between the three systems studied in this notebook can now be understood as follows:

```
                    Raw CSI
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
    Time View    Spatial View    Frequency View
        │              │              │
        ▼              ▼              ▼
    Doppler         AoA            ToF
        │              │              │
        └───────┬──────┴──────────────┘
                ▼
       Wireless Environment
```

Each method extracts only a subset of the available information.

This observation motivates the central idea of our project:

Rather than choosing between SpotFi, Widar, or DeepFi, we propose to preserve and fuse their complementary representations.

---

# 5.12 Research Note

One of the key insights gained during this project was recognizing that all CSI-based sensing methods are fundamentally different projections of the same underlying wireless channel.

- Widar emphasizes temporal dynamics to recover motion.
- SpotFi exploits spatial and frequency diversity to recover geometry.
- DeepFi learns latent representations from amplitude and phase patterns.

This suggests that their outputs should be complementary rather than competitive.

Instead of replacing one method with another, a future architecture can fuse these representations together, potentially reducing the information loss associated with any individual pipeline.

---

# Looking Ahead

We now know **what information exists** inside CSI.

The next question is:

> **Why can't we use raw CSI directly?**

Before any geometry or motion can be estimated, the measurements must be calibrated to remove hardware-induced distortions.

The next chapter begins our detailed reconstruction of the Widar 3.0 signal processing pipeline, starting with CSI phase calibration and conjugate multiplication.