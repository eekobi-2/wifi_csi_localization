# Chapter 4 : Understanding OFDM and Channel State Information (CSI)

> **Question**
>
> If the wireless channel contains information about the environment, how does a WiFi receiver actually measure it?

---

# 4.1 Motivation

In the previous chapter, we established that the environment modifies every transmitted electromagnetic wave.

Instead of a single propagation path,

multiple reflected copies arrive at the receiver,

resulting in a channel impulse response

$$
h(t).
$$

Unfortunately,

modern WiFi hardware cannot directly observe

$$
h(t).
$$

Instead,

WiFi standards such as IEEE 802.11n use a modulation technique called

**Orthogonal Frequency Division Multiplexing (OFDM)**

to estimate the channel in the frequency domain.

The output of this estimation process is called

**Channel State Information (CSI).**

This chapter explains exactly how CSI is generated.

---

# 4.2 Why Single Carrier Communication Fails Indoors

Suppose we transmit a single high-speed signal

```
Tx ---------------------> Rx
```

In an indoor environment,

multiple delayed copies arrive

```
Tx
 │
 ├──────────────► Rx
 │
 ├────Wall──────► Rx
 │
 ├────Human─────► Rx
 │
 └────Table─────► Rx
```

Each copy arrives with a different delay

$$
\tau_1,\tau_2,\ldots,\tau_L.
$$

These delayed copies overlap.

The receiver therefore cannot distinguish

where one transmitted symbol ends

and another begins.

This phenomenon is called

**Inter-Symbol Interference (ISI).**

ISI severely limits communication speed.

---

# 4.3 The OFDM Solution

Instead of transmitting one very fast carrier,

OFDM divides the available bandwidth into

many narrowband carriers called

**subcarriers.**

```
Entire Bandwidth

|--------------------------------|

Single Carrier

██████████████████████████████████


OFDM

██ ██ ██ ██ ██ ██ ██ ██ ██ ██ ██
```

Each subcarrier carries data independently.

Since every subcarrier occupies only a small bandwidth,

its channel appears approximately constant.

Instead of estimating one complicated channel,

the receiver estimates

many nearly-flat channels.

---

# 4.4 Orthogonality

At first glance,

placing many carriers close together seems impossible.

Wouldn't they interfere?

The answer is no.

OFDM chooses carrier frequencies such that

they are mathematically orthogonal.

If

$$
f_k=\frac{k}{T},
$$

then

$$
\int_0^T
e^{j2\pi f_i t}
e^{-j2\pi f_j t}
dt
=
0
\quad
(i\neq j)
$$

This orthogonality allows

dozens of carriers

to occupy the same spectrum

without interfering.

---

# 4.5 Frequency Domain View

Instead of transmitting

```
One Carrier
```

OFDM transmits

```
Subcarrier 1

Subcarrier 2

Subcarrier 3

...

Subcarrier N
```

Each subcarrier experiences

its own complex channel gain

$$
H(f_k).
$$

The receiver estimates

every one of these gains independently.

---

# 4.6 Channel Frequency Response

Recall that

$$
h(t)
$$

describes the channel in time.

Taking its Fourier Transform gives

$$
H(f) =\mathcal {F}\{h(t)\}
$$

called the

**Channel Frequency Response (CFR).**

Every OFDM subcarrier samples

one point of this function.

```
H(f)

^

│        •
│
│   •
│             •
│
│ •
│______________________________>

      Frequency
```

Each dot is one subcarrier.

Collectively,

they approximate

the entire channel.

---

# 4.7 What is CSI?

Channel State Information (CSI)

is simply

the sampled Channel Frequency Response.

Mathematically,

$$
CSI
=
\{
H(f_1),
H(f_2),
...
H(f_N)
\}
$$

Each CSI value is a

**complex number**

$$
H
=
A
e^{j\phi}
$$

where

- $A$ is the signal amplitude
- $\phi$ is the signal phase

Both quantities contain physical information.

---

# 4.8 Amplitude and Phase

Every CSI measurement consists of

Amplitude

```
Reflection
Shadowing
Attenuation
Path Loss
```

and

Phase

```
Propagation Delay

Path Length

Multipath

Motion

AoA

ToF
```

This explains why

most WiFi sensing algorithms spend considerable effort

calibrating

the phase measurements.

---

# 4.9 CSI Tensor

An Intel 5300 NIC reports CSI for

- 30 subcarriers
- multiple receive antennas
- multiple transmit antennas

For one packet,

the CSI tensor has dimensions

```
(Subcarriers,
Receive Antennas,
Transmit Antennas)

(30,3,2)
```

For an entire recording,

we observed

```
(1445,30,3,2)
```

meaning

```
1445 packets

↓

30 subcarriers

↓

3 receive antennas

↓

2 transmit antennas
```

Each entry is one complex number

$$
A e^{j\phi}
$$

which completely characterizes

that subcarrier

for that antenna pair

at that instant.

---

# 4.10 Our Dataset

Using the Python package

```
csiread
```

we loaded the Widar dataset

and observed

```python
csi.csi.shape

(1445,30,3,2)
```

For a single packet

```python
packet = csi.csi[0]

packet.shape

(30,3,2)
```

Thus,

each packet contains

```
30

×

3

×

2

=

180
```

complex channel measurements.

These measurements are the only information

available to every algorithm

that follows.

SpotFi,

DeepFi,

and Widar

all begin with exactly this tensor.

Their differences lie entirely in

how they process it.

---

# 4.11 CSI is an Inverse Problem

Notice something remarkable.

The receiver never measures

- walls
- people
- distance
- velocity
- angle

It measures only

180 complex numbers.

Everything else

must be inferred.

```
Environment

↓

Propagation

↓

CSI

↓

Signal Processing

↓

Recovered Information
```

Different algorithms recover different quantities

from exactly the same measurements.

---

# 4.12 Research Note

During our implementation,

one important realization was that

the CSI tensor itself never changes between algorithms.

Whether using

- SpotFi,
- Widar,
- DeepFi,

or our proposed architecture,

the input remains identical.

The algorithms differ only in

which physical properties they attempt to recover

from the same complex measurements.

This observation motivated our later proposal

to combine multiple representations

instead of relying on a single one.

---

# Connection to the Next Chapters

We now understand that CSI consists of

complex measurements

across

- subcarriers,
- antennas,
- packets.

The next logical question becomes

> **How much physical information is actually hidden inside these complex numbers?**

This question leads directly to the quantities exploited by modern CSI sensing systems:

- Amplitude
- Phase
- Angle of Arrival (AoA)
- Time of Flight (ToF)
- Doppler Shift
- Micro-Doppler

These quantities form the foundation of SpotFi, Widar, and DeepFi.
