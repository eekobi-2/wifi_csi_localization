# Chapter 3 : From Electromagnetic Waves to Channel State Information

> **Question**
>
> How does a wireless communication signal become a sensor of the physical world?

---

# 3.1 Introduction

Before studying WiFi Channel State Information (CSI), it is important to understand a more fundamental question.

When a WiFi transmitter sends data, its objective is simply to communicate with another device. Nothing in the communication protocol explicitly attempts to measure walls, people, furniture, or moving objects.

Yet remarkably, modern WiFi sensing systems can estimate

- indoor location,
- human motion,
- breathing,
- gestures,
- occupancy,
- walking direction,
- velocity,
- Angle of Arrival (AoA),
- Time of Flight (ToF),

using exactly the same communication signals.

This naturally raises the question

> **Where does all of this information come from?**

The answer is simple.

**It is created by physics.**

Communication algorithms merely measure it.

---

# 3.2 Electromagnetic Waves

WiFi is an electromagnetic wave.

Like every electromagnetic wave, it satisfies Maxwell's equations.

Although the complete derivation is beyond the scope of this notebook, one important consequence is that electromagnetic waves transport

- energy,
- momentum,
- phase,
- frequency,
- polarization,

through space.

Whenever these waves encounter an object, their propagation changes.

Therefore the received signal always contains information about every object encountered along its propagation path.

---

# 3.3 Propagation in Free Space

Imagine an empty room containing only

- one transmitter
- one receiver

```
Tx -------------------------- Rx
```

Only one propagation path exists.

The received signal is simply

$$
r(t)=\alpha s(t-\tau)
$$

where

- $s(t)$ is the transmitted waveform,
- $\alpha$ is the propagation attenuation,
- $\tau$ is the propagation delay.

In this ideal world,

localization would be trivial.

Unfortunately,

real indoor environments never behave this way.

---

# 3.4 Multipath Propagation

Now place several objects inside the room.

```
                Ceiling
   _________________________________

        Wall

Tx  --------------->------------- Rx
  \             /
   \           /
    \ Table   /
     \       /
      Human

```

The transmitted wave no longer follows a single path.

Instead,

multiple copies of the same waveform arrive at the receiver.

Each copy

- travels a different distance,
- experiences different attenuation,
- accumulates different phase,
- arrives from a different direction.

The received signal therefore becomes

$$
r(t)=
\sum_{i=1}^{L}
\alpha_i
s(t-\tau_i)
$$

where

- $L$ is the number of propagation paths.

This equation is arguably the most important equation in WiFi sensing.

Almost every CSI-based sensing algorithm is ultimately trying to estimate the parameters

$$
(\alpha_i,\tau_i,\theta_i,f_{D,i})
$$

for every propagation path.

---

# 3.5 Static and Dynamic Multipath

Not every propagation path behaves the same way.

Indoor environments naturally contain

## Static paths

Examples include

- walls
- ceiling
- furniture
- floor
- shelves

These remain nearly constant over time.

Their contribution to the wireless channel changes very slowly.

---

## Dynamic paths

Moving objects introduce new propagation paths.

Examples include

- walking people
- rotating machinery
- opening doors
- moving robots
- drones

These paths change continuously.

Their changing propagation distance introduces

- Doppler shift
- phase variation
- amplitude variation

These dynamic paths are precisely the signals exploited by Widar.

---

# 3.6 Every Physical Quantity Leaves a Signature

Every interaction between an electromagnetic wave and the environment modifies a different property of the received signal.

| Environmental Quantity | Signal Signature |
|-------------------------|------------------|
| Distance | Propagation delay |
| Reflection | Amplitude |
| Path length | Phase |
| Arrival direction | Relative antenna phase |
| Motion | Doppler frequency |
| Small body movement | Micro-Doppler |
| Multipath | Multiple delayed copies |

Instead of directly measuring objects,

WiFi sensing measures these signatures.

The challenge is to invert the process.

```
Environment

↓

Propagation

↓

Wireless Channel

↓

CSI

↓

Signal Processing

↓

Estimated Environment
```

Everything after CSI is essentially an inverse problem.

---

# 3.7 The Wireless Channel

Rather than describing every propagation path individually,

wireless communications combine all paths into a single mathematical object called the **channel**.

The channel completely describes how the environment transforms the transmitted waveform.

Instead of writing

$$
r(t)=\sum_i \alpha_i s(t-\tau_i)
$$

communication theory writes

$$
r(t)=h(t)*s(t)
$$

where

- $*$ denotes convolution,
- $h(t)$ is the channel impulse response.

The channel therefore contains the combined effect of

- every wall,
- every reflection,
- every moving object,
- every propagation path.

This observation is fundamental.

> **If the environment changes, the channel changes.**

---

# 3.8 Frequency Domain Representation

Modern WiFi does not estimate

$$
h(t)
$$

directly.

Instead,

it estimates its Fourier Transform

$$
H(f)
=
\mathcal{F}
\{
h(t)
\}
$$

This frequency-domain representation is called the

**Channel Frequency Response (CFR).**

Each OFDM subcarrier samples

one point of this frequency response.

Collectively,

these sampled frequency responses become

**Channel State Information (CSI).**

This is the mathematical origin of CSI.

It is simply the sampled frequency response of the wireless channel.

---

# 3.9 Research Note

One of the most important conceptual shifts during this project was realizing that

WiFi sensing does **not** create new information.

Instead,

the information already exists inside the wireless channel because electromagnetic waves have interacted with the surrounding environment.

Algorithms such as SpotFi, Widar, and DeepFi merely recover different subsets of that information.

This observation motivates the remainder of this notebook.

Rather than studying individual algorithms independently, we will interpret each algorithm as recovering a different physical property encoded within the same wireless channel.

---

# What's Next?

Now that we understand how the environment modifies the wireless channel,

the next chapter asks

> **How is the wireless channel represented digitally inside an Intel 5300 WiFi card?**

That chapter introduces

- OFDM,
- subcarriers,
- Channel Frequency Response,
- Channel State Information (CSI),

and connects the underlying physics to the actual CSI matrices that we parsed from the Widar 3.0 dataset.