# Chapter 2 : The Physics of WiFi Sensing

---

## 2.1 Why Can WiFi Sense the Environment?

At first glance, WiFi appears to be nothing more than a wireless communication system whose purpose is to transmit data between devices. Surprisingly, the same wireless signals used for communication also contain detailed information about the surrounding environment.

The central question of this chapter is therefore:

> **Why does a WiFi signal contain information about objects, people, and the environment through which it propagates?**

Understanding the answer to this question forms the foundation of every CSI-based sensing algorithm discussed later in this notebook.

Rather than beginning with machine learning or signal processing, we first study the physical origin of the information contained inside WiFi signals.

---

## 2.2 Electromagnetic Waves Carry Information

A WiFi transmitter radiates an electromagnetic wave.

As this wave propagates through space, it continuously interacts with the surrounding environment.

Depending on the material and geometry of nearby objects, the wave may

- propagate directly,
- reflect,
- diffract,
- scatter,
- or be partially absorbed.

Consequently, the receiver rarely observes a single propagation path.

Instead, it receives many delayed and attenuated copies of the transmitted waveform.

Each propagation path carries information about

- the distance traveled,
- the direction from which it arrived,
- the attenuation experienced,
- the phase accumulated during propagation.

Therefore, the received signal is effectively a superposition of many propagation paths.

The wireless channel is not merely a communication medium—it is a physical measurement of the surrounding environment.

---

## 2.3 Every Object Modifies the Wireless Channel

Every object inside the environment changes the propagation of electromagnetic waves.

For example,

| Object | Effect on WiFi Signal |
|---------|----------------------|
| Wall | Strong reflection and attenuation |
| Metal Shelf | High reflection |
| Human Body | Reflection, absorption and scattering |
| Moving Person | Time-varying Doppler shift |
| Furniture | Static multipath |
| Door Opening | Changes propagation paths |

This means that even if the transmitter continuously sends the same signal, the received waveform changes whenever the environment changes.

Instead of viewing these variations as noise, WiFi sensing algorithms attempt to interpret them as measurements of the environment itself.

---

## 2.4 The Wireless Channel Becomes a Sensor

Traditional communication systems attempt to estimate the wireless channel only to compensate for its distortion.

WiFi sensing takes the opposite approach.

Instead of removing the channel, it attempts to estimate physical properties of the environment directly from the channel.

This represents a fundamental shift in perspective.

Communication viewpoint:

```
Transmitter
      ↓
 Wireless Channel (undesired distortion)
      ↓
 Equalization
      ↓
 Recover transmitted data
```

WiFi sensing viewpoint:

```
Transmitter
      ↓
 Wireless Channel
      ↓
 Measure the channel
      ↓
 Recover information about the environment
```

The wireless channel itself becomes the sensing modality.

---

## 2.5 Why CSI Exists

Modern WiFi standards use Orthogonal Frequency Division Multiplexing (OFDM).

Instead of transmitting information over one carrier frequency, OFDM divides the available bandwidth into many narrow subcarriers.

Each subcarrier experiences the wireless channel slightly differently.

The receiver therefore estimates the complex channel response of every subcarrier.

These complex measurements are collectively called

**Channel State Information (CSI).**

Instead of producing a single received power measurement (RSSI), CSI provides a complex response

$$
H(f)=A(f)e^{j\phi(f)}
$$

for every measured subcarrier.

Each CSI measurement therefore contains

- amplitude
- phase

for one OFDM subcarrier.

Across all subcarriers, CSI forms a detailed frequency-domain description of the wireless channel.

---

## 2.6 What Information Exists Inside CSI?

Although CSI is simply a collection of complex numbers, those numbers encode several physical properties of the environment.

Some examples include

| Physical Quantity | Observable in CSI |
|-------------------|------------------|
| Signal attenuation | Amplitude |
| Phase delay | Phase |
| Propagation distance | Time of Flight (ToF) |
| Arrival direction | Angle of Arrival (AoA) |
| Relative motion | Doppler Frequency |
| Human motion | Micro-Doppler |
| Multipath propagation | Complex channel response |

These quantities form the basis of nearly every WiFi sensing algorithm developed over the past decade.

Different algorithms simply choose to estimate different subsets of this information.

---

## 2.7 Different Papers Recover Different Information

One of the most important observations made during this project is that no single CSI sensing algorithm extracts all available information from the wireless channel.

Instead, each algorithm focuses on one aspect of the channel.

| Method | Primary Information Recovered |
|---------|------------------------------|
| SpotFi | Geometry (AoA + ToF) |
| Widar 3.0 | Motion (Doppler + Velocity Spectrum) |
| DeepFi | Learned CSI Representation |

This observation motivates the remainder of the notebook.

Rather than viewing these methods as competing approaches, we instead view them as complementary techniques that recover different physical properties from the same underlying CSI measurements.

---

## 2.8 Research Goal

our goal is to understand

- what information exists inside CSI,
- how different algorithms recover different portions of that information,
- what information is discarded by each method,
- and how those complementary representations may eventually be fused into a unified perception framework.

The remainder of this notebook progressively studies each of these approaches, beginning with the mathematical description of CSI itself.

---