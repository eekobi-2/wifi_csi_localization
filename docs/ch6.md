# Chapter 6 : From Raw CSI to Meaningful Signals

> **Question**
>
> If CSI already contains all the information about the environment, why can't we simply feed it directly into a neural network?

---

# 6.1 Motivation

At this point we understand that CSI contains information about

- propagation delay,
- multipath,
- Angle of Arrival (AoA),
- Doppler,
- Time of Flight (ToF),
- human motion.

However, the CSI reported by commodity WiFi hardware is **not** a perfect measurement of the wireless channel.

Instead, it is affected by numerous hardware imperfections introduced by

- transmitter oscillator,
- receiver oscillator,
- packet synchronization,
- automatic gain control (AGC),
- carrier frequency offset (CFO),
- sampling frequency offset (SFO),
- packet detection delay,
- thermal noise.

Consequently, the CSI obtained from an Intel 5300 NIC is a noisy estimate of the true wireless channel.

The objective of the signal processing pipeline is therefore **not to create information**, but rather to suppress hardware artifacts while preserving the physical variations caused by the environment.

---

# 6.2 Overall Signal Processing Pipeline

The Widar 3.0 preprocessing pipeline can be summarized as

```text
                     Raw CSI
                        │
                        ▼
              CSI Tensor Parsing
                        │
                        ▼
          Reference Antenna Selection
                        │
                        ▼
             Amplitude Adjustment
                        │
                        ▼
          Conjugate Multiplication
                        │
                        ▼
          Butterworth Band-pass Filter
                        │
                        ▼
              Principal Component Analysis
                        │
                        ▼
          Time-Frequency Analysis (STFT)
                        │
                        ▼
               Doppler Spectrum
                        │
                        ▼
               Velocity Mapping
                        │
                        ▼
              Velocity Spectrum
                        │
                        ▼
                  CNN + GRU
```

Throughout this chapter we reconstruct every stage from the original MATLAB implementation and reproduce it in Python.

---

# 6.3 Raw CSI Tensor

Using the Intel 5300 CSI Tool and the `csiread` library, we parsed a Widar 3.0 recording.

The resulting tensor has dimensions

```python
csi.csi.shape

(1445, 30, 3, 2)
```

which corresponds to

| Dimension | Meaning |
|-----------|---------|
| 1445 | Number of packets |
| 30 | OFDM subcarriers |
| 3 | Receive antennas |
| 2 | Transmit antennas |

Each element of this tensor is a complex value

$$
H=Ae^{j\phi}
$$

containing the measured channel response between one transmitter–receiver antenna pair for one subcarrier.

---

# 6.4 Understanding the Tensor Layout

Before implementing the Widar pipeline, we verified how `csiread` stores the CSI.

For a single packet

```python
packet = csi.csi[0]
```

the tensor shape is

```python
(30,3,2)
```

Flattening the first transmit stream gives

```python
packet[:,:,0].T.reshape(-1)
```

which produces

```text
Rx1
Subcarrier 1 ... 30

↓

Rx2
Subcarrier 1 ... 30

↓

Rx3
Subcarrier 1 ... 30
```

This ordering exactly matches the assumptions made in the original Widar implementation.

Verifying this ordering was essential because every subsequent processing step assumes that the 90 CSI streams are grouped by receive antenna.

---

# 6.5 Visualizing Raw CSI

The first step in our exploration was simply plotting the raw measurements.

We visualized

- real component,
- imaginary component,
- amplitude,
- phase,

for every subcarrier.

These plots revealed several important observations.

## Observation 1

Different subcarriers exhibit different amplitudes even within the same packet.

This confirms that each OFDM subcarrier experiences a different channel response.

---

## Observation 2

Phase measurements appear highly irregular.

Unlike amplitude,

raw phase cannot be directly interpreted because it contains hardware-induced offsets.

This motivates the calibration steps introduced later.

---

## Observation 3

Packets collected over time show gradual changes,

indicating that temporal information is preserved.

This temporal evolution later becomes the basis for Doppler estimation.

---

# 6.6 Why Raw CSI Cannot Be Used Directly

A natural question arises.

Why not simply train a neural network using

```text
Raw CSI

↓

CNN

↓

Prediction
```

Although this approach is possible,

it suffers from several drawbacks.

First,

hardware distortions dominate the measurements.

Second,

static reflections often have much larger amplitudes than dynamic reflections.

Third,

neighboring subcarriers are highly correlated.

Finally,

many CSI streams contain almost identical information.

Consequently,

the neural network must first learn to remove hardware artifacts before learning the actual sensing task.

Instead,

Widar removes these artifacts using deterministic signal processing before applying deep learning.

This significantly reduces the burden placed on the neural network.

---

# 6.7 Research Philosophy of Widar

One of the most interesting observations during our study was that Widar follows a fundamentally different philosophy from many recent deep learning systems.

Instead of

```text
Raw Data

↓

Large Neural Network

↓

Prediction
```

Widar performs

```text
Physics-based Signal Processing

↓

Meaningful Physical Representation

↓

Small Neural Network
```

The signal processing stage attempts to expose quantities that are already known to be physically meaningful, such as Doppler frequency and velocity.

The neural network is then responsible for learning patterns within this reduced and more informative representation.

This design improves interpretability and reduces the amount of data required for training.

---

# 6.8 Research Note

During the implementation of the Widar pipeline, we deliberately avoided treating the MATLAB code as a black box.

Instead, each processing stage was implemented independently and verified using intermediate visualizations and numerical checks.

This approach not only ensured correctness but also clarified the physical role of every operation in the pipeline.

By the end of this chapter, every component of the Widar preprocessing stage had been reproduced and understood individually before being combined into the complete signal processing chain.

---

# Looking Ahead

The next section begins with the first processing stage:

> **How does Widar automatically choose the best reference antenna, and why is a reference antenna needed at all?**

---

## Complete Pipeline

Raw CSI

↓

Tensor Parsing

↓

Reference Antenna Selection

↓

Amplitude Adjustment

↓

Conjugate Multiplication

↓

Butterworth Filtering

↓

Principal Component Analysis

↓

Short Time Fourier Transform

↓

Doppler Spectrum

↓

Velocity Mapping

↓

CNN-GRU

For every block i will explain

- What
- Why
- Mathematics
- Implementation
- Output Shape

---

# 6.9 Reference Antenna Selection

---

## Motivation

Question

Why do we need a reference antenna?

Physical intuition

Imagine three antennas

Rx1

Rx2

Rx3

One antenna experiences

high SNR

stable channel

less fading

Another antenna

low SNR

large fluctuations

If we use the unstable antenna as reference

phase subtraction becomes noisy.

Therefore Widar first finds the most stable antenna.

---


## Mathematics

For antenna i

Compute

μ

σ

Score

μ / σ

Interpretation

Large μ

↓

High received energy

Small σ

↓

Stable channel

Large μ/σ

↓

Best reference


---

## Python Implementation

Explain every tensor shape.

1445 × 90

↓

reshape

↓

1445 × 30 × 3

↓

Mean

↓

Variance

↓

Score

↓

argmax

---

## Complexity

O(N)

---

## Limitations

Single global antenna.

May fail when environment changes.

---


# 6.10 Amplitude Adjustment

> **Question**
>
> Why does Widar modify the amplitudes of the CSI measurements before any signal processing?
>
> Why are two seemingly strange operations performed?
>
> - Subtract the minimum amplitude from every CSI stream.
> - Add a constant bias to the reference antenna.
>
> What physical problem are these operations trying to solve?

---

# 6.10.1 Motivation

After selecting the reference antenna, Widar performs an amplitude calibration step before computing the conjugate multiplication.


Why should subtracting the minimum amplitude improve Doppler estimation?

Why should the reference antenna suddenly become much larger?

Understanding these two operations is essential before moving to conjugate multiplication.

---

# 6.10.2 Reminder: CSI Representation

Each CSI measurement is a complex number

$$
H=Ae^{j\phi}
$$

where

- $A$ denotes the measured amplitude.
- $\phi$ denotes the measured phase.

The amplitude and phase together describe the wireless channel.

During amplitude adjustment, Widar intentionally modifies **only the amplitude** while preserving the original phase.

---

# 6.10.3 Original MATLAB Implementation

The original Widar implementation processes every CSI stream independently.

### Step 1

Compute the amplitude

```matlab
amp = abs(csi_data(:,jj));
```

---

### Step 2

Find the smallest non-zero amplitude

```matlab
alpha = min(amp(amp~=0));
```

---

### Step 3

Subtract this minimum value

```matlab
abs(abs(csi_data(:,jj))-alpha)
```

---

### Step 4

Restore the original phase

```matlab
exp(1j*angle(csi_data(:,jj)))
```

giving

$$
H_{\mathrm{adj}} = (|H| - \alpha)e^{j\phi}
$$

---

# 6.10.4 Physical Interpretation

Every CSI stream contains

- useful dynamic reflections,
- static reflections,
- hardware gain,
- measurement noise.

The smallest observed amplitude is usually produced by the weakest measurable channel response.

Subtracting this minimum shifts every CSI stream toward a common baseline.

Conceptually,

```
Before

Amplitude

^

│          *
│       *
│   *
│ *
└────────────────>

After subtraction

^

│      *
│   *
│ *
└────────────────>
```

The objective is **not** to normalize the signal.

Instead,

the objective is to reduce the influence of the weakest static component.

---

# 6.10.5 Why Not Normalize?

A natural question is

> Why doesn't Widar simply divide every CSI stream by its maximum amplitude?

Although such normalization is common in machine learning,

it changes the relative magnitude between different CSI streams.

Those relative magnitudes contain useful propagation information.

Widar therefore performs only a small baseline correction instead of complete normalization.

---

# 6.10.6 Computing β

After adjusting every CSI stream,

Widar computes

```matlab
beta =
1000 * alpha_sum / (30 * rx_acnt);
```

where

- `alpha_sum` is the sum of all minimum amplitudes,
- `30` is the number of subcarriers,
- `rx_acnt` is the number of receive antennas.

Therefore

$$
\beta = 1000 \times \mathrm{Average}(\alpha)
$$

Notice that Widar deliberately multiplies the average by

```
1000
```

This immediately raises another question.

> Why make the reference antenna one thousand times stronger?

---

# 6.10.7 Reference Antenna Enhancement

The adjusted reference antenna becomes

$$
H_{\mathrm{ref}} = (|H| + \beta)e^{j\phi}
$$

Unlike the previous operation,

the amplitude is increased rather than decreased.

Conceptually,

```
Original Reference

^

│      *
│   *
│ *
└──────────>

Adjusted Reference

^

│
│
│
│                     *
│                 *
│             *
└────────────────────────────>
```

The phase remains unchanged,

but the magnitude becomes significantly larger.

---

# 6.10.8 Why Increase the Reference Amplitude?

The next stage computes

$$
H_i \cdot H_{\mathrm{ref}}^{*}
$$

where

- one signal comes from the dynamic antenna,
- one comes from the reference antenna.

If the reference signal were weak,

its measurement noise would also be multiplied.

Increasing the reference amplitude causes the reference channel to dominate the multiplication,

making the resulting phase difference more stable.

Although Widar does not explicitly discuss this design choice,

it is consistent with the subsequent conjugate multiplication stage.

---

# 6.10.9 Phase Preservation

One important property of this operation is that **phase is completely preserved.**

Suppose

$$
H=Ae^{j\phi}.
$$

After amplitude adjustment,

$$
H^{\prime} = A^{\prime} e^{j\phi}
$$

Therefore

$$
\angle\!\left(H^{\prime}\right) = \phi
$$

Only the amplitude changes.

The propagation phase remains exactly the same.

This is extremely important because Doppler estimation depends almost entirely on phase evolution.

---

# 6.10.10 Verification

During implementation we numerically verified that the phase remained unchanged.

```python
np.max(
    np.abs(
        np.angle(ref_adj)-phase_ref
    )
)
```

returned approximately

```text
1.11 × 10⁻¹⁶
```

which is numerical floating-point precision.

Initially,

a much larger phase error appeared for the non-reference antennas.

This was eventually traced to

**phase wrapping** rather than an error in the amplitude adjustment itself.

---

# 6.10.11 Python Implementation

The MATLAB code was translated directly into Python.

```python
amp = np.abs(csi_streams)

alpha = np.min(amp[amp > 0])

amp_adj = np.maximum(amp - alpha, 0)

adj_csi = amp_adj * np.exp(1j * np.angle(csi_streams))
```

For the reference antenna

```python
beta = 1000 * np.mean(alpha_values)

ref_adj = (
    np.abs(reference_csi) + beta
) * np.exp(1j * np.angle(reference_csi))
```

The resulting tensors preserve the original complex phase while modifying only the amplitudes.

---

# 6.10.12 Computational Complexity

For each CSI stream,

the algorithm performs

- one minimum search,
- one subtraction,
- one complex reconstruction.

Therefore,

for

- $$N$$ packets,
- $$S$$ CSI streams,

the computational complexity is

$$
O(NS).
$$

This stage is computationally inexpensive compared to PCA or STFT.

---

# 6.10.13 Advantages

- Extremely simple.
- Preserves phase exactly.
- Reduces baseline amplitude.
- Produces a stronger reference signal.
- Easy to reproduce.

---

# 6.10.14 Limitations

Several questions remain unanswered by the original paper.

- Why is the minimum amplitude the best baseline estimate?
- Why is the scaling factor exactly **1000**?
- Would adaptive scaling perform better?
- Could amplitude calibration be learned automatically?

These questions are not addressed in the original Widar implementation.

---

# 6.10.15 Research Notes

During reproduction we initially assumed that amplitude adjustment would also modify the phase.

However,

because the operation only changes the magnitude,

the phase remains mathematically unchanged.

The apparent discrepancies observed during implementation were caused by phase wrapping rather than by the calibration itself.

This implementation step also highlighted an interesting design philosophy of Widar.

Instead of relying on a neural network to learn robust amplitude representations,

the authors explicitly engineer a physically motivated preprocessing step before any learning occurs.

---

# Beyond the Paper

The original Widar implementation uses two manually chosen parameters:

- the minimum amplitude α,
- the scaling constant β.

Possible research directions include

1. Learning the amplitude calibration directly from data.

2. Replacing the fixed scaling factor with an adaptive estimator.

3. Using an attention mechanism to estimate the reference confidence.

4. Jointly optimizing amplitude calibration together with the downstream neural network.

Such approaches may preserve more information while remaining fully differentiable.


# 6.11 Conjugate Multiplication

> **Question**
>
> Why does Widar multiply one CSI stream with the complex conjugate of another?
>
> Why not simply subtract the two signals?
>
> Why is this operation the foundation of Doppler estimation?

---

# 6.11.1 Motivation

After amplitude adjustment, Widar possesses

- one **reference CSI stream**, and
- multiple **dynamic CSI streams**.

The next objective is to suppress disturbances that are common to both antennas while emphasizing the differences caused by motion.

Instead of subtracting amplitudes or phases directly, Widar computes the **complex conjugate multiplication**

$$
H_i H_{ref}^{*}.
$$

Although the MATLAB implementation consists of only a single line,

```matlab
conj_mult = csi_data_adj .* conj(csi_data_ref_adj);
```

this operation is arguably the most important step in the entire Widar signal processing pipeline.

It converts CSI from an absolute measurement into a **relative measurement** between two antennas.

---

# 6.11.2 Revisiting the CSI Representation

Consider two calibrated CSI measurements

Dynamic antenna

$$
H_d=A_de^{j\phi_d}
$$

Reference antenna

$$
H_r=A_re^{j\phi_r}
$$

where

-$$A$$ denotes amplitude
- $$\phi$$ denotes phase.

Our objective is to compare these two signals.

---

# 6.11.3 Why Not Subtract?

The simplest idea might be

$$
H_d-H_r.
$$

Unfortunately,

this subtraction mixes

- amplitude,
- phase,
- noise,

in a complicated manner.

Furthermore,

phase is circular.

For example,

```
179°

and

−179°
```

represent almost identical physical directions,

yet simple subtraction gives

```
358°
```

which is meaningless.

A different operation is required.

---

# 6.11.4 Complex Conjugate

Recall that

$$
H=Ae^{j\phi}.
$$

Its complex conjugate is

$$
H^{*}=Ae^{-j\phi}.
$$

Notice that

only the sign of the phase changes.

The amplitude remains identical.

---

# 6.11.5 Derivation

Now compute

$$
H_dH_r^{*}
$$

Substituting the two CSI measurements,

$$
= A_d e^{j\phi_d} \cdot A_r e^{-j\phi_r}
$$

Combining amplitudes,

$$
= A_d A_r e^{j(\phi_d - \phi_r)}
$$

This equation is extremely important.

Instead of preserving

the two original phases,

the multiplication preserves only

their **difference**

$$
\Delta\phi = \phi_d - \phi_r
$$

---

# 6.11.6 Interpretation

This operation performs two tasks simultaneously.

## Amplitude

The new amplitude becomes

$$
A_dA_r
$$

which depends on both channels.

---

## Phase

The new phase becomes

$$
\phi_d-\phi_r.
$$

Instead of measuring

absolute phase,

we now measure

relative phase.

This relative phase is considerably more stable.

---

# 6.11.7 Why Relative Phase Matters

Raw CSI phase contains

- oscillator offsets,
- packet timing offsets,
- synchronization errors,
- hardware imperfections.

Many of these errors are **common** to all receive antennas because they originate from shared hardware.

Suppose

$$
\phi_d = \phi_{\mathrm{true}} + \phi_{\mathrm{noise}}
$$

and

$$
\phi_r = \phi_{\mathrm{ref}} + \phi_{\mathrm{noise}}
$$

Then

$$
\phi_d - \phi_r = \phi_{\mathrm{true}} - \phi_{\mathrm{ref}}
$$

The common hardware phase

cancels automatically.

This is the primary reason Widar performs conjugate multiplication.

---

# 6.11.8 Physical Interpretation

Imagine a person walking.

```
Tx

↓

Human

↓

Rx1

↓

Rx2
```

As the person moves,

the propagation distance changes.

Consequently,

both antennas observe changing phases.

However,

the hardware-induced phase errors remain nearly identical.

By subtracting the two phases,

the motion-induced phase variation becomes much more visible.

Conjugate multiplication therefore transforms CSI into a representation that emphasizes **relative motion** rather than absolute hardware phase.

---

# 6.11.9 MATLAB Implementation

The original Widar implementation performs

```matlab
conj_mult = csi_data_adj .* conj(csi_data_ref_adj);
```

Immediately afterwards,

the reference antenna itself is discarded.

```matlab
conj_mult = [
conj_mult(:,1:30*(idx-1))
conj_mult(:,30*idx+1:90)
];
```

Since the reference multiplied by itself would produce

$$
A_r^2e^{j0},
$$

it contains no useful phase difference.

Only the remaining antennas are retained.

---

# 6.11.10 Python Implementation

Our implementation follows the MATLAB code exactly.

```python
conj_mult = other_adj * np.conj(ref_adj)
```

where

- `other_adj`

contains the calibrated dynamic antennas,

and

- `ref_adj`

contains the repeated reference antenna.

After multiplication,

the reference antenna channels are removed,

leaving

```
1445

×

60
```

complex CSI streams.

---

# 6.11.11 Tensor Shapes

Before multiplication

```
Reference

1445 × 90
```

```
Dynamic

1445 × 90
```

After removing the reference antenna

```
1445 × 60
```

Each column corresponds to

- one subcarrier
- one non-reference antenna.

These 60 streams become the input to the Butterworth filters.

---

# 6.11.12 Verification

During implementation we verified

```python
conj_mult.shape
```

returned

```text
(1445,60)
```

matching the original MATLAB implementation.

We also confirmed that

the operation preserved complex values,

allowing both amplitude and relative phase to be analyzed in later stages.

---

# 6.11.13 Why Multiplication Instead of Explicit Phase Difference?

One might ask,

why not compute

```python
phase_other-phase_ref
```

instead?

The answer is subtle.

Complex multiplication naturally preserves

- amplitude,
- phase,
- complex continuity,

without requiring explicit phase unwrapping.

Furthermore,

subsequent signal processing

(PCA and STFT)

operates directly on the complex-valued signal.

Thus,

conjugate multiplication produces a mathematically cleaner representation than manipulating phase alone.

---

# 6.11.14 Computational Complexity

The operation consists of

one complex multiplication

per packet

per CSI stream.

Therefore,

for

- $$N$$ packets,
- $$S$$ streams,

the complexity is

$$
O(NS).
$$

This stage is computationally inexpensive.

---

# 6.11.15 Advantages

- Removes common phase offsets.
- Produces a relative phase measurement.
- Preserves complex-valued information.
- Simple to implement.
- Highly efficient.

---

# 6.11.16 Limitations

Conjugate multiplication does **not**

- estimate Doppler,
- remove static clutter,
- perform localization,
- estimate velocity.

It merely produces a cleaner representation.

Static reflections still remain and are removed later by filtering.

---

# Paper

The original Widar implementation performs conjugate multiplication immediately after amplitude adjustment and before any filtering or PCA.

No further explanation is provided in the paper regarding this design choice.

---

# Our Interpretation

Conjugate multiplication transforms CSI into a relative phase representation where hardware-induced phase errors shared across antennas are significantly reduced.

This provides a more stable signal for subsequent Doppler estimation while preserving the temporal dynamics introduced by moving objects.

---

# Research Notes

While implementing this stage, one important realization was that **conjugate multiplication is not the Doppler estimator**.

Instead,

it is a **phase calibration step**.

Only after

- Butterworth filtering,
- PCA,
- and STFT

does the Doppler spectrum emerge.

Understanding this distinction clarified the purpose of the subsequent processing stages.

---

# Beyond the Paper

Several interesting research questions arise from this stage.

1. Can the reference antenna be learned dynamically instead of selected using a fixed μ/σ criterion?

2. Could a complex-valued neural network learn a better relative representation than handcrafted conjugate multiplication?

3. Is pairwise conjugate multiplication between all antenna pairs more informative than using a single reference antenna?

4. Can graph-based message passing between antennas preserve richer spatial relationships than the current reference-based formulation?

These questions may lead to alternative CSI representations that retain more geometric information while still suppressing hardware-induced phase errors.

# 6.12 Butterworth Filtering

> **Question**
>
> After conjugate multiplication, why isn't the signal ready for Doppler estimation?
>
> Why does Widar remove both low-frequency and high-frequency components before performing the STFT?

---

# 6.12.1 Motivation

Conjugate multiplication removes a large portion of the hardware-induced phase offsets between antennas.

However, the resulting signal still contains contributions from

- static objects,
- slowly varying environmental changes,
- thermal noise,
- electronic noise,
- dynamic reflections from moving humans.

The objective of this stage is therefore **not** to estimate motion.

Instead, it attempts to suppress signal components that are unlikely to originate from human movement.

Only after this filtering stage does the CSI primarily represent dynamic motion inside the environment.

---

# 6.12.2 What Frequencies Exist Inside CSI?

Suppose a WiFi transmitter continuously illuminates a room.

The received CSI changes because different objects interact with the electromagnetic wave.

Different objects introduce different temporal frequencies.

| Object | Frequency Content |
|----------|------------------|
| Wall | ~0 Hz |
| Floor | ~0 Hz |
| Ceiling | ~0 Hz |
| Furniture | ~0 Hz |
| Slowly drifting hardware offsets | Very Low Frequency |
| Walking person | Few Hz to tens of Hz |
| Running person | Higher Doppler frequencies |
| Electronic noise | Broad-band high frequency |

This observation is extremely important.

The CSI signal contains

```
Useful Motion

+

Static Reflections

+

Noise
```

Our objective is to isolate only the first component.

---

# 6.12.3 Static Clutter

Consider a completely empty room.

```
Tx

────────────► Rx
```

Nothing moves.

The propagation paths remain constant.

Therefore,

the CSI phase remains nearly constant over time.

A nearly constant signal corresponds to

```
Frequency ≈ 0 Hz
```

This component is called

**Static Clutter**.

Examples include

- walls,
- tables,
- shelves,
- ceiling,
- floor.

Although these objects produce strong reflections,

they do not contribute useful Doppler information.

---

# 6.12.4 Human Motion

Now suppose a person walks through the room.

```
Tx

↓

Walking Person

↓

Rx
```

The propagation distance changes continuously.

Consequently,

the phase evolves with time,

producing oscillations.

Unlike static clutter,

these oscillations occur at non-zero frequencies.

The Doppler signature of human motion therefore appears away from DC (0 Hz).

This is exactly the information Widar wishes to preserve.

---

# 6.12.5 Why Two Filters?

After conjugate multiplication,

the signal still contains

```
Very Low Frequency Components

+

Human Motion

+

High Frequency Noise
```

Therefore Widar applies two filters sequentially.

```
Raw CSI

↓

Low-pass

↓

High-pass
```

Together these filters form a **band-pass filter**.

The objective is

```
Keep Human Motion

Remove Everything Else
```

---

# 6.12.6 Original MATLAB Implementation

The filter coefficients are computed as

```matlab
samp_rate = 1000;

half_rate = samp_rate / 2;

uppe_orde = 6;
uppe_stop = 60;

lowe_orde = 3;
lowe_stop = 2;

[lu,ld] = butter(uppe_orde,uppe_stop/half_rate,'low');

[hu,hd] = butter(lowe_orde,lowe_stop/half_rate,'high');
```

For every CSI stream,

```matlab
conj_mult(:,jj)=filter(lu,ld,conj_mult(:,jj));

conj_mult(:,jj)=filter(hu,hd,conj_mult(:,jj));
```

---

# 6.12.7 Low-Pass Filter

The first filter removes frequencies above

```
60 Hz
```

This suppresses

- thermal noise,
- electronic noise,
- rapid fluctuations.

The original MATLAB implementation uses

```
6th Order Butterworth
```

with

```
Cutoff = 60 Hz
```

---

# 6.12.8 High-Pass Filter

The second filter removes

frequencies below

```
2 Hz
```

These components primarily originate from

- static reflections,
- stationary objects,
- slowly varying hardware drift.

The original MATLAB implementation uses

```
3rd Order Butterworth
```

with

```
Cutoff = 2 Hz
```

---

# 6.12.9 Effective Frequency Band

After applying both filters,

the retained signal approximately occupies

```
2 Hz

↓

60 Hz
```

Conceptually,

```
Before

0--------------------------------100 Hz

██████████████████████████████████

After

0--------------------------------100 Hz

      ███████████████████
      2               60
```

Only frequencies inside this region continue through the Widar pipeline.

---

# 6.12.10 Why Butterworth?

Many digital filters exist.

Examples include

- Chebyshev
- Elliptic
- Bessel
- Butterworth

Widar chooses a Butterworth filter because its passband is maximally flat.

This minimizes amplitude distortion within the frequencies of interest.

Since Doppler estimation depends on preserving relative amplitudes across time,

a smooth passband is desirable.

---

# 6.12.11 Python Implementation

The MATLAB implementation translates directly into SciPy.

```python
from scipy.signal import butter
from scipy.signal import lfilter

fs = 1000

low_b, low_a = butter(
    6,
    60/(fs/2),
    btype="low"
)

high_b, high_a = butter(
    3,
    2/(fs/2),
    btype="high"
)

filtered = np.zeros_like(conj_mult)

for i in range(conj_mult.shape[1]):

    x = lfilter(low_b, low_a, conj_mult[:, i])

    x = lfilter(high_b, high_a, x)

    filtered[:, i] = x
```

This implementation exactly follows the Widar MATLAB pipeline.

---

# 6.12.12 Tensor Shape

Before filtering

```
1445 × 60
```

After filtering

```
1445 × 60
```

Filtering changes

- signal content

but

does **not** change tensor dimensions.

---

# 6.12.13 Interpretation

After filtering,

the CSI no longer primarily represents

```
Environment
```

Instead,

it primarily represents

```
Motion
```

This distinction is important.

Filtering transforms

```
Communication Signal

↓

Motion Signal
```

which is exactly what Widar requires.

---

# 6.12.14 Advantages

- Removes static clutter.
- Suppresses hardware drift.
- Removes high-frequency noise.
- Preserves human motion frequencies.
- Extremely efficient.

---

# 6.12.15 Limitations

The filter parameters are fixed.

Questions naturally arise.

- Why exactly 2 Hz?
- Why exactly 60 Hz?
- Would different activities require different cutoffs?
- Can adaptive filters improve performance?
- Can the filter itself be learned?

The original paper does not investigate these questions.

---

# Paper

The released Widar MATLAB implementation applies

- 6th-order Butterworth low-pass filter
- 3rd-order Butterworth high-pass filter

before PCA and STFT.

The resulting signal is then forwarded to the next processing stage.

---

# Our Interpretation

This stage performs frequency selection rather than feature extraction.

Its primary purpose is to isolate frequency components associated with human motion while suppressing static reflections and electronic noise.

Consequently,

subsequent stages such as PCA and STFT operate on a much cleaner representation of the dynamic channel.

---

# Research Notes

One important realization during reproduction was that filtering alone does **not** estimate Doppler.

It merely removes frequency components that are unlikely to correspond to meaningful human motion.

The Doppler spectrum is still hidden inside the filtered signal and will only become visible after applying the Short-Time Fourier Transform (STFT).

This distinction clarified why Widar performs PCA and STFT after filtering rather than directly on the raw CSI.

---

# Beyond the Paper

Several research directions emerge from this stage.

1. Learn the filter coefficients directly from data.

2. Replace Butterworth filters with differentiable convolutional filters.

3. Use adaptive filtering based on the estimated activity.

4. Investigate wavelet denoising instead of fixed band-pass filtering.

5. Preserve multiple frequency bands rather than discarding information outside a fixed range.

These ideas may allow future systems to retain more information while remaining robust to environmental changes.

---

# 6.13 Principal Component Analysis (PCA)

> **Question**
>
> After filtering, Widar still has 60 complex CSI streams.
>
> Why doesn't it compute the Doppler spectrum for every stream separately?
>
> Why does it first compress all streams into a single signal using Principal Component Analysis (PCA)?

---

# 6.13.1 Motivation

At this stage of the Widar pipeline we have

```
Raw CSI

↓

Reference Antenna Selection

↓

Amplitude Adjustment

↓

Conjugate Multiplication

↓

Band-pass Filtering

↓

60 Complex CSI Streams
```

Each CSI stream represents

- one receive antenna,
- one OFDM subcarrier,
- one temporal sequence.

Although these streams are different,

they are **not independent**.

Every stream observes

- the same moving human,
- the same environment,
- the same propagation geometry,

only through slightly different channels.

This immediately suggests that a large amount of information is redundant.

---

# 6.13.2 Why Not Process Every Stream Independently?

Suppose we compute an STFT for every CSI stream.

```
60 CSI Streams

↓

60 STFTs

↓

60 Doppler Spectra
```

This approach has several disadvantages.

- Large computational cost.
- Many Doppler spectra contain almost identical information.
- Some streams have poor SNR.
- Some streams are dominated by static clutter.
- Later fusion becomes difficult.

Instead,

Widar attempts to construct a **single representative signal**

before performing the STFT.

---

# 6.13.3 Observation

After filtering,

many CSI streams look remarkably similar.

Conceptually,

```
CSI Stream 1

~~~~~~~^^^^^^~~~~~~

CSI Stream 2

~~~~~~~^^^^^^~~~~~~

CSI Stream 3

~~~~~~~^^^^^^~~~~~~

CSI Stream 4

~~~~~~~^^^^^^~~~~~~
```

Although amplitudes differ,

the underlying motion pattern is almost identical.

This suggests that all streams are observing the same latent phenomenon.

The objective of PCA is therefore

> Find the direction in which the CSI varies the most.

---

# 6.13.4 Correlation Between CSI Streams

The strongest source of variation in the filtered CSI is

**human motion**.

Since every receive antenna observes the same moving person,

their temporal variations become correlated.

Mathematically,

the CSI matrix can be written as

$$
X \in \mathbb{C}^{N \times 60}
$$

where

- $$N$$ is the number of packets,
- 60 is the number of filtered CSI streams.

Each column represents

one temporal CSI signal.

PCA attempts to discover the dominant correlations among these columns.

---

# 6.13.5 What Does PCA Actually Do?

Rather than viewing each CSI stream independently,

PCA asks

> Is there a new coordinate system in which most of the signal energy is concentrated into only a few dimensions?

Instead of

```
60 correlated variables
```

it attempts to produce

```
1 dominant variable

+

59 weak variables
```

The first variable should contain most of the motion information.

---

# 6.13.6 Covariance Matrix

PCA begins by computing the covariance matrix.

For a complex-valued CSI matrix

$$
X
$$

the covariance matrix is

$$
R = X^{H} X
$$

where

- $$H$$ denotes the Hermitian transpose (conjugate transpose).

Unlike real-valued PCA,

complex PCA preserves both

- amplitude,
- phase.

This distinction is essential because phase contains the Doppler information.

---

# 6.13.7 Eigenvalue Decomposition

Next,

PCA solves

$$
R v_i = \lambda_i v_i
$$

where

- $$\lambda_i$$ is an eigenvalue,
- $$v_i$$ is the corresponding eigenvector.

Each eigenvector defines

a new coordinate axis.

Each eigenvalue measures

how much signal variance lies along that axis.

---

# 6.13.8 Selecting the Principal Component

The eigenvalues are sorted

```
λ₁ ≥ λ₂ ≥ λ₃ ≥ ...
```

The first eigenvector

$$
v_1
$$

corresponds to the direction of maximum variance.

Widar keeps only this eigenvector.

The filtered CSI is projected onto it.

$$
y = X v_1
$$

The result is

one complex-valued signal

instead of

sixty.

---

# 6.13.9 Why Only One Component?

A natural question is

> Why throw away the remaining 59 components?

The intuition is simple.

Most of the remaining components represent

- residual noise,
- measurement uncertainty,
- weak reflections,
- less informative variations.

The dominant principal component is assumed to contain

the strongest motion signature.

Since the objective is Doppler estimation,

keeping only the strongest component significantly reduces computational cost.

---

# 6.13.10 Original MATLAB Implementation

The original Widar implementation performs

```matlab
pca_coef = pca(conj_mult);

conj_mult_pca = conj_mult * pca_coef(:,1);
```

Notice something interesting.

The authors never explicitly compute

- covariance,
- eigenvalues,
- eigenvectors.

MATLAB's `pca()` performs all of these internally.

The resulting first principal component becomes the only signal passed to the STFT.

---

# 6.13.11 Our First Python Attempt

Initially,

we attempted

```python
from sklearn.decomposition import PCA

pca = PCA(n_components=1)

conj_mult_pca = pca.fit_transform(conj_mult)
```

This immediately failed with

```
ComplexWarning

Casting complex values to real
discards imaginary part
```

This error turned out to be extremely important.

---

# 6.13.12 Why sklearn Failed

Scikit-learn assumes

```
Real-valued PCA
```

Internally,

it converts

```
complex

↓

real
```

discarding the imaginary component.

For ordinary machine learning,

this behaviour is acceptable.

For CSI,

it is catastrophic.

The imaginary component contains

- phase,
- Doppler,
- propagation information.

Discarding it destroys the physical meaning of the signal.

---

# 6.13.13 Why MATLAB Worked

MATLAB supports PCA for complex matrices by operating on the Hermitian covariance matrix.

Consequently,

both

- real,
- imaginary,

components participate in the decomposition.

This preserves the complex-valued structure of the CSI.

---

# 6.13.14 Our Python Implementation

To reproduce MATLAB,

we implemented complex PCA manually.

```python
R = conj_mult.conj().T @ conj_mult

eigvals, eigvecs = np.linalg.eigh(R)

idx = np.argsort(eigvals)[::-1]

v1 = eigvecs[:, idx[0]]

conj_mult_pca = conj_mult @ v1
```

This implementation exactly follows the mathematical definition of complex PCA.

Unlike scikit-learn,

it preserves

- amplitude,
- phase,
- complex correlations.

---

# 6.13.15 Tensor Shapes

Before PCA

```
1445 × 60
```

After PCA

```
1445 × 1
```

This single complex time series becomes the input to the Short-Time Fourier Transform.

---

# 6.13.16 Interpretation

PCA is **not** extracting Doppler.

It is simply answering

> Which combination of all CSI streams best represents the observed motion?

Only after this projection is the signal transformed into the frequency domain.

---

# 6.13.17 Advantages

- Large dimensionality reduction.
- Removes redundant CSI streams.
- Improves signal-to-noise ratio.
- Preserves dominant motion.
- Reduces STFT computation by approximately 60×.

---

# 6.13.18 Limitations

Several assumptions are implicit.

- Largest variance corresponds to human motion.
- Motion dominates noise.
- One principal component is sufficient.
- Linear combinations adequately describe the CSI.

These assumptions may not hold

in crowded environments

or

when multiple people move simultaneously.

---

# Paper

The released Widar implementation computes PCA immediately after filtering and retains only the first principal component before computing the STFT.

No detailed explanation is provided regarding the use of complex-valued PCA.

---

# Our Interpretation

PCA acts as a spatial fusion mechanism.

Instead of selecting one antenna,

it constructs a weighted combination of all filtered CSI streams.

The dominant principal component represents the direction in signal space where human motion produces the largest variation.

This projection provides a cleaner and more compact representation for subsequent Doppler estimation.

---

# Research Notes

Implementing PCA revealed an important distinction between generic machine learning libraries and signal processing toolkits.

Although both MATLAB and scikit-learn provide a function called `PCA`, they do not operate on complex-valued data in the same manner.

Reproducing the Widar pipeline therefore required implementing complex PCA manually using the Hermitian covariance matrix and eigenvalue decomposition.

This implementation preserves the phase information required for Doppler estimation.

---

# Beyond the Paper

The PCA stage raises several interesting research questions.

1. Can PCA be replaced with a learnable complex-valued attention mechanism?

2. Instead of selecting only the first principal component, can multiple components be preserved and fused adaptively?

3. Can graph neural networks model correlations between CSI streams more effectively than PCA?

4. Would a complex-valued transformer learn a richer latent representation without requiring explicit dimensionality reduction?

5. Can the projection matrix itself be optimized jointly with the downstream localization or activity recognition network?

These questions suggest several directions for replacing handcrafted linear dimensionality reduction with modern representation learning while preserving the underlying physics of the CSI measurements.

---

# 6.14 Short-Time Fourier Transform (STFT)

> **Question**
>
> After PCA, we have a single complex CSI signal representing the dominant motion in the environment.
>
> Why can't we simply compute one Fourier Transform to obtain the Doppler frequencies?
>
> Why does Widar perform a Short-Time Fourier Transform (STFT) instead?

---

# 6.14.1 Motivation

At this stage, the Widar pipeline has reduced the original 60 filtered CSI streams into a single complex-valued time series.

```
Raw CSI

↓

Reference Selection

↓

Amplitude Adjustment

↓

Conjugate Multiplication

↓

Butterworth Filtering

↓

Complex PCA

↓

One Complex Signal
```

The remaining task is to determine

- **what frequencies are present**, and
- **when they occur**.

The second requirement is critical.

Human motion is **not stationary**.

Walking,

stopping,

turning,

raising a hand,

or sitting down

all produce Doppler frequencies that change continuously with time.

Therefore, Widar requires a representation that preserves both

- frequency,
- and time.

---

# 6.14.2 What is Doppler?

Suppose a person walks toward the receiver.

The propagation distance continuously decreases.

Consequently,

the received phase changes continuously.

A changing phase corresponds to a changing frequency.

This frequency is called the **Doppler Frequency**.

Unlike a pure sinusoid,

human motion rarely produces

one constant Doppler frequency.

Instead,

the Doppler frequency evolves throughout the activity.

For example,

```
Walking

Time →

20 Hz

18 Hz

15 Hz

10 Hz

5 Hz

Stop

0 Hz
```

The frequency itself changes with time.

---

# 6.14.3 Why FFT Fails

The ordinary Fourier Transform assumes

the signal is

**stationary**.

In other words,

it assumes that the frequency content does not change during the observation period.

For example,

consider

```
Signal

10 Hz

↓

10 Hz

↓

10 Hz

↓

10 Hz
```

A single FFT correctly reports

```
10 Hz
```

Now consider

```
Walking

5 Hz

↓

12 Hz

↓

18 Hz

↓

10 Hz

↓

3 Hz
```

What does the FFT report?

It reports

```
5

10

12

18
```

but provides **no indication of when these frequencies occurred**.

The temporal information is completely lost.

---

# 6.14.4 Time-Frequency Analysis

To estimate human motion,

we need to know

```
Frequency

AND

Time
```

simultaneously.

Instead of asking

> Which frequencies exist?

we ask

> Which frequencies exist **at this particular instant**?

This naturally leads to

Time-Frequency Analysis.

---

# 6.14.5 Sliding Window Concept

The fundamental idea is surprisingly simple.

Instead of analyzing

the entire signal,

analyze only

a small portion.

```
Entire Signal

□□□□□□□□□□□□□□□□□□□□□□□□□□□□□□

Window

██████

↓

Move Window

  ██████

↓

Move Again

      ██████
```

For every window,

compute one FFT.

This produces

one frequency spectrum

per time instant.

---

# 6.14.6 Mathematical Formulation

Suppose

the PCA output is

$$
x[n].
$$

Instead of computing

$$
X(f) = \sum_{n} x[n]\,e^{-j2\pi f n}
$$

we first multiply the signal by a window

$$
w[n].
$$

The resulting transform becomes

$$
\mathrm{STFT}(t, f) = \sum_{n=-\infty}^{\infty} x[n]\,w[n - t]\,e^{-j2\pi f n}
$$

The window

selects only a small portion of the signal,

allowing the frequency content to evolve over time.

---

# 6.14.7 Time-Frequency Resolution

The window length determines

a fundamental trade-off.

Large window

```
Excellent Frequency Resolution

Poor Time Resolution
```

Small window

```
Excellent Time Resolution

Poor Frequency Resolution
```

This is known as the **time-frequency uncertainty principle**.

No transform can simultaneously achieve arbitrarily high resolution in both domains.

Choosing the window length therefore depends on the application.

---

# 6.14.8 Why a Gaussian Window?

The Widar MATLAB implementation computes

```matlab
window_size = round(samp_rate/4 + 1);

freq_time_prof_allfreq =
tfrsp(
    conj_mult_pca,
    time_instance,
    samp_rate,
    tftb_window(window_size,'gauss')
);
```

Rather than using a rectangular window,

Widar employs a

Gaussian window.

A Gaussian window gradually attenuates the signal near the edges,

reducing spectral leakage and producing a smoother time-frequency representation.

---

# 6.14.9 Original MATLAB Implementation

The original implementation performs

```matlab
time_instance = 1:length(conj_mult_pca);

window_size = round(samp_rate/4+1);

freq_time_prof_allfreq =
tfrsp(
    conj_mult_pca,
    time_instance,
    samp_rate,
    tftb_window(window_size,'gauss')
);
```

The custom MATLAB function `tfrsp()` computes the spectrogram by

1. Sliding a Gaussian window across the signal.
2. Computing the FFT within each window.
3. Squaring the magnitude.
4. Returning the complete time-frequency representation.

---

# 6.14.10 Our Python Implementation

For reproduction, the MATLAB implementation can be approximated using SciPy's STFT.

```python
from scipy.signal import stft

f, t, Zxx = stft(
    conj_mult_pca,
    fs=1000,
    window="gaussian",
    nperseg=251
)

doppler = np.abs(Zxx)
```

This produces a complex-valued time-frequency matrix.

The magnitude of this matrix represents the Doppler energy at every time-frequency location.

---

# 6.14.11 Tensor Shapes

Before STFT

```
1445 × 1
```

After STFT

```
Frequency Bins

×

Time Frames
```

Instead of

one temporal signal,

we now obtain

a **2D Doppler image**.

This image becomes the input to the velocity mapping stage.

---

# 6.14.12 Doppler Spectrum

The STFT output can be visualized as

```
Frequency

↑

|

|

|

+------------------------→ Time
```

Every pixel represents

the signal energy

at a particular

- frequency,
- time.

Unlike the FFT,

this representation preserves

the temporal evolution of human motion.

---

# 6.14.13 Frequency Selection

The STFT initially computes

the entire frequency spectrum.

However,

Widar retains only

the frequencies within the previously selected passband.

This produces

the final Doppler spectrum

used for later processing.

---

# 6.14.14 Spectrum Normalization

The original MATLAB implementation performs

```matlab
freq_time_prof =
abs(freq_time_prof);

freq_time_prof =
freq_time_prof ./ ...
sum(abs(freq_time_prof),1);
```

Each time slice is normalized independently.

This removes overall amplitude variations between different time windows,

making the Doppler spectrum depend primarily on

the relative energy distribution across frequencies.

---

# 6.14.15 Interpretation

The STFT does **not** estimate velocity.

It estimates

the **Doppler spectrum**.

In other words,

it answers

> At this instant, which Doppler frequencies are present?

Velocity estimation is still one stage away.

---

# 6.14.16 Advantages

- Preserves temporal information.
- Suitable for non-stationary signals.
- Produces a two-dimensional representation.
- Directly captures evolving Doppler signatures.

---

# 6.14.17 Limitations

Several assumptions remain.

- Window length is fixed.
- Frequency resolution is limited.
- Time-frequency uncertainty cannot be avoided.
- Multiple moving objects may overlap in the spectrogram.

These limitations motivate the nonlinear velocity mapping stage used later in Widar.

---

# Paper

The released Widar MATLAB implementation computes a Gaussian-window Short-Time Fourier Transform after PCA and before velocity mapping.

The resulting time-frequency representation is interpreted as the Doppler spectrum.

---

# Our Interpretation

The STFT is the first stage in the Widar pipeline where the motion becomes visually interpretable.

Up to this point, every processing step was aimed at cleaning, calibrating, and compressing the CSI.

The STFT converts the one-dimensional complex signal into a two-dimensional image whose structure directly reflects the temporal evolution of human motion.

This representation is considerably easier to interpret and subsequently process than the original CSI.

---

# Research Notes

While reproducing the MATLAB implementation, we examined the original `tfrsp()` source code rather than treating it as a black box.

This revealed that the function is fundamentally a Gaussian-window spectrogram implementation, allowing us to construct an equivalent Python version using SciPy while preserving the overall processing philosophy.

Understanding the implementation clarified that Widar does not perform any specialized Doppler transform at this stage—the Doppler spectrum emerges naturally from the STFT applied to the calibrated CSI signal.

---

# Beyond the Paper

Several opportunities for improvement emerge.

1. Replace the STFT with a Continuous Wavelet Transform (CWT) for improved multi-scale time-frequency resolution.

2. Investigate adaptive window lengths based on the observed motion.

3. Explore learnable time-frequency representations using neural networks.

4. Compare STFT with modern synchrosqueezing transforms for sharper Doppler localization.

5. Preserve the complex STFT coefficients instead of using only their magnitude.

These directions may improve the representation of complex human motions while retaining more information from the original CSI signal.

---

# 6.15 From Doppler Spectrum to Velocity Spectrum

> **Question**
>
> After computing the Doppler spectrum, why doesn't Widar directly classify gestures?
>
> Why introduce an expensive nonlinear optimization step?

---

# 6.15.1 Motivation

The output of the previous chapter was

```
Complex CSI

↓

STFT

↓

Doppler Spectrum
```

At first glance,

this appears to be sufficient.

The Doppler spectrum already contains

- positive Doppler,
- negative Doppler,
- motion intensity,
- temporal evolution.

Why perform another transformation?

The answer lies in a fundamental ambiguity.

**The Doppler spectrum tells us how fast the signal frequency changed, not how the object actually moved in space.**

Recovering motion from Doppler alone is therefore an inverse problem.

---

# 6.15.2 Doppler is Not Velocity

Consider a person walking.

```
Tx  --------------------------  Rx

             Person
```

Suppose the person walks

- directly toward the receiver,
- diagonally,
- perpendicular to the transmitter-receiver line.

Even if the walking speed is identical,

the measured Doppler frequencies will be different.

Why?

Because Doppler measures only the component of velocity projected onto the propagation path.

Mathematically,

```
True Velocity

↓

Projection

↓

Measured Doppler
```

The STFT therefore measures only a projection of the true motion.

---

# 6.15.3 The Inverse Problem

The objective is now

```
Observed Doppler Spectrum

↓

?

↓

True Velocity Distribution
```

Instead of asking

> "What Doppler frequencies exist?"

Widar asks

> "What velocity field could have produced these Doppler frequencies?"

This is a much harder problem.

---

# 6.15.4 Physical Geometry

Unlike many deep learning approaches,

Widar explicitly incorporates knowledge of the room geometry.

The algorithm assumes

- transmitter position,
- receiver positions,
- torso position.

```
             Rx2

Rx1                    Rx3


          Human


Tx
```

Because these positions are known,

the relationship between motion and Doppler can be computed analytically.

---

# 6.15.5 The A Matrix

The first step is constructing the matrix

```matlab
A = get_A_matrix(
    torso_pos,
    Tx_pos,
    Rx_pos,
    rx_cnt
);
```

For every receiver,

the matrix stores

```
Direction

from

Transmitter

↓

Torso

+

Torso

↓

Receiver
```

The MATLAB implementation computes

```matlab
A(ii,:) =
(torso-Tx)/||torso-Tx||

+

(torso-Rx)/||torso-Rx||
```

Thus,

each row of **A**

represents the propagation direction associated with one receiver.

---

# 6.15.6 Interpretation of A

Suppose

```
Velocity

vx

vy
```

Then

```
A

×

Velocity
```

computes

the component of motion observed by that receiver.

The A matrix therefore converts

```
2D Velocity

↓

Projected Motion
```

This is the physical bridge between geometry and Doppler.

---

# 6.15.7 Doppler Equation

The Doppler frequency is given by

$$
f_D = \frac{\mathbf{A}\mathbf{v}}{\lambda}
$$

where

- $\mathbf{v}$ is the velocity vector,
- $\lambda$ is the wavelength.

This equation tells us

how every possible velocity maps into Doppler frequency.

---

# 6.15.8 Discretizing Velocity

Instead of estimating

every possible velocity,

Widar discretizes velocity space.

```matlab
Vmin = -2

Vmax = 2

Vbins = 20
```

producing

```
20 × 20
```

velocity cells.

```
vy

↑

□ □ □ □ □

□ □ □ □ □

□ □ □ □ □

□ □ □ □ □

────────────→ vx
```

Each square corresponds to

one possible velocity vector.

---

# 6.15.9 Velocity-to-Doppler Mapping Matrix

For every velocity cell,

the MATLAB code computes

```matlab
VDM =
get_velocity2doppler_mapping_matrix(...)
```

The resulting tensor has dimensions

```
20

×

20

×

Receivers

×

Frequency Bins
```

Every element answers

> If motion occurred at this velocity,

which Doppler frequency would be observed?

This tensor is the forward model of the sensing system.

---

# 6.15.10 Forward Model

Suppose

```
Velocity Spectrum

↓

VDM

↓

Predicted Doppler Spectrum
```

This forward model is deterministic.

If the velocity distribution is known,

the Doppler spectrum can be computed directly.

Unfortunately,

our problem is the opposite.

We know the Doppler spectrum

and wish to estimate

the velocity spectrum.

---

# 6.15.11 Inverse Problem

Therefore,

Widar solves

```
Unknown Velocity Spectrum

↓

Forward Model

↓

Predicted Doppler

↓

Compare

↓

Observed Doppler
```

The optimization searches for

the velocity spectrum

whose predicted Doppler spectrum most closely matches

the measured one.

---

# 6.15.12 Optimization Variable

The unknown quantity is

```
P
```

where

```
P

=

20 × 20
```

Every element represents

the probability (or intensity)

that motion occurred with that velocity.

Thus,

the optimization is not estimating

a single velocity,

but an entire velocity distribution.

---

# 6.15.13 MATLAB Objective

The optimization is

```matlab
P = fmincon(
    @(P)
    DVM_target_func(...)
)
```

This function minimizes

the difference between

```
Predicted Doppler

and

Observed Doppler
```

while enforcing sparsity.

---

# 6.15.14 Important Observation

Notice something remarkable.

The neural network has not yet appeared.

Everything until this point is

pure

- geometry,
- optimization,
- signal processing.

Only after the optimization finishes

does Widar invoke deep learning.

---

# Paper

The published Widar implementation explicitly reconstructs a velocity spectrum before performing activity recognition.

The velocity spectrum is obtained by solving a nonlinear optimization problem constrained by the known transmitter and receiver geometry.

---

# Our Interpretation

This optimization is the defining characteristic of Widar.

Rather than asking a neural network to infer geometry,

the authors encode the geometry analytically.

The neural network therefore receives a representation that is already physically meaningful.

This significantly reduces the learning burden compared to end-to-end approaches operating directly on raw CSI.

---

# Research Notes

While studying the MATLAB implementation, one conceptual distinction became clear.

The STFT does not estimate velocity.

It estimates Doppler frequency.

The optimization is responsible for converting this Doppler information into a spatial velocity distribution by incorporating the known sensing geometry.

Understanding this distinction made the purpose of the velocity mapping stage much clearer than the brief description provided in the original paper.

---

# Beyond the Paper

This stage is arguably the strongest candidate for replacement by modern learning-based methods.

Potential research directions include

1. Learning the Doppler-to-Velocity mapping using a neural network.

2. Replacing the nonlinear optimization with a differentiable physics layer.

3. Incorporating uncertainty in transmitter and receiver locations.

4. Learning the geometry jointly with the representation.

5. Predicting the velocity spectrum using a transformer conditioned on both Doppler and CSI.

These ideas preserve the physical insights of Widar while reducing the computational cost of solving an optimization problem for every temporal segment.


# 6.16 Understanding the Velocity Mapping Optimization

> **Question**
>
> We now have the Doppler spectrum obtained from the STFT.
>
> Why is another optimization required?
>
> What exactly is Widar optimizing?
>
> What does the optimization variable represent?

---

# 6.16.1 Motivation

The output of the previous stage is

```
CSI

↓

Filtering

↓

PCA

↓

STFT

↓

Doppler Spectrum
```

The Doppler spectrum already tells us

- positive Doppler frequencies,
- negative Doppler frequencies,
- motion intensity.

So why perform another optimization?

The answer lies in one simple fact.

> **The Doppler spectrum is an observation.**

It is **not** the underlying physical quantity we ultimately want.

The quantity we actually seek is

```
Human Velocity
```

Therefore,

the objective becomes

```
Observed Doppler

↓

Inverse Problem

↓

Velocity Distribution
```

---

# 6.16.2 Forward Problems vs Inverse Problems

It is useful to distinguish between two classes of problems.

## Forward Problem

Suppose we already know

- human velocity,
- transmitter location,
- receiver locations.

Physics allows us to predict

```
Velocity

↓

Propagation Geometry

↓

Expected Doppler Spectrum
```

This is called the **forward model**.

---

## Inverse Problem

In reality,

we observe

```
Measured Doppler Spectrum
```

and wish to estimate

```
Velocity
```

This is considerably harder because multiple velocity distributions may produce similar Doppler spectra.

This is the problem solved by Widar.

---

# 6.16.3 Discretizing Velocity Space

Instead of estimating a continuous velocity,

Widar discretizes the velocity space.

```matlab
V_min = -2;

V_max = 2;

V_bins = 20;
```

The resulting velocity grid becomes

```
20 × 20
```

```
vy

↑

□ □ □ □ □

□ □ □ □ □

□ □ □ □ □

□ □ □ □ □

──────────────→ vx
```

Each square corresponds to

one candidate velocity vector

$$
(v_x,v_y).
$$

---

# 6.16.4 What is P?

The optimization variable is

$$
P
$$

whose dimensions are

```
20 × 20
```

Every element

$$
P(i,j)
$$

represents

the intensity associated with velocity

$$
(v_x^{(i)},v_y^{(j)}).
$$

Notice something important.

Widar does **not**

estimate

one velocity.

Instead,

it estimates

an entire

**velocity distribution.**

---

# 6.16.5 Why a Velocity Distribution?

Imagine two moving body parts.

```
Torso

↓

Walking Right

Hand

↓

Swinging Left
```

Different body parts generate different Doppler frequencies.

A single velocity vector cannot explain such motion.

A velocity distribution can.

---

# 6.16.6 Constructing the Geometry Matrix

The MATLAB code computes

```matlab
A = get_A_matrix(...)
```

Inside the function

```matlab
A(ii,:) =
(torso-Tx)/||torso-Tx||

+

(torso-Rx)/||torso-Rx||
```

For every receiver,

A stores

```
Unit Vector

Tx → Human

+

Unit Vector

Human → Receiver
```

---

# 6.16.7 Interpretation of A

Suppose

```
Velocity

vx

vy
```

Then

```
A

×

Velocity
```

returns

the projected motion

along the propagation path.

Therefore,

A converts

```
2D Motion

↓

Observed Radial Motion
```

This is the geometric bridge between velocity and Doppler.

---

# 6.16.8 Doppler Equation

For a given velocity

$$
\mathbf{v} =
\begin{bmatrix}
v_x \\
v_y
\end{bmatrix}
$$

the expected Doppler frequency becomes

$$
f_D = \frac{A\mathbf{v}}{\lambda}
$$

where

- A depends on geometry.
- λ is the carrier wavelength.

This equation forms the basis of the entire optimization.

---

# 6.16.9 Building the Velocity-to-Doppler Mapping Matrix

The MATLAB function

```matlab
get_velocity2doppler_mapping_matrix(...)
```

loops over

```
Every Receiver

↓

Every Velocity Cell

↓

Every Doppler Bin
```

For each velocity

it computes

```matlab
plcr_hz =
round(
A*v
/
wave_length
)
```

If the Doppler frequency lies inside the valid range,

the corresponding entry becomes

```
1
```

otherwise

```
0
```

The result is a four-dimensional tensor

```
VDM

20

×

20

×

Receivers

×

Frequency Bins
```

---

# 6.16.10 Physical Meaning of VDM

The VDM tensor answers

> **If motion occurred at this velocity,
>
> which Doppler frequency would we observe?**

Think of VDM as a lookup table derived from physics.

It does not depend on the measured CSI.

It depends only on

- geometry,
- wavelength,
- receiver locations.

---

# 6.16.11 Constructing the Forward Model

Suppose

the velocity spectrum is

$$
P.
$$

Each non-zero element contributes energy

to one Doppler bin.

Summing every contribution gives

```
Predicted Doppler Spectrum
```

The MATLAB implementation computes

```matlab
doppler_spectrum_seg_approximate =
squeeze(
sum(
sum(
P .* VDM
)
)
);
```

Conceptually,

```
Velocity Spectrum

↓

Projection

↓

Receiver 1 Doppler

Receiver 2 Doppler

...

Receiver N Doppler
```

---

# 6.16.12 Optimization Objective

The optimization now compares

```
Observed Doppler

↓

Predicted Doppler
```

If the two match,

the estimated velocity distribution is considered correct.

The optimization therefore minimizes

```
Prediction Error
```

---

# 6.16.13 Why Earth Mover's Distance?

Instead of comparing every Doppler bin independently,

Widar computes

```matlab
(abs(pred-target)
*
triu(ones(F,F)))
```

This accumulates errors across neighboring bins.

Suppose

```
Prediction

19 Hz

Target

20 Hz
```

A simple squared error would treat these as completely different.

The cumulative formulation recognizes

that

19 Hz

and

20 Hz

are physically very similar.

This makes the optimization considerably more robust.

Although the MATLAB code does not explicitly call it Earth Mover's Distance,

the cumulative difference resembles a one-dimensional EMD formulation.

---

# 6.16.14 Sparsity Regularization

The objective also includes

```matlab
lambda

×

sum(P~=0)
```

or

```matlab
lambda

×

sum(P)
```

depending on the selected norm.

The intuition is straightforward.

Human motion usually occupies

only a few velocity cells.

Therefore,

the recovered velocity spectrum should remain sparse.

Without regularization,

the optimization could distribute small values across many cells,

producing unrealistic motion patterns.

---

# 6.16.15 Why fmincon?

The optimization variable

contains

```
20 × 20

=

400

unknowns.
```

The objective is nonlinear,

contains box constraints,

and includes sparsity regularization.

The MATLAB implementation therefore uses

```matlab
fmincon

↓

SQP Algorithm
```

Sequential Quadratic Programming iteratively solves local quadratic approximations until convergence.

---

# 6.16.16 Final Output

After optimization,

the solution

```
P

20 × 20
```

becomes

```
Velocity Spectrum
```

Conceptually,

```
vy

↑

████

██

█

────────────→ vx
```

Bright regions correspond to

velocities that best explain

the observed Doppler spectrum.

---

# 6.16.17 Why CNN Instead of Using P Directly?

One might ask

> If we already recovered the velocity spectrum,
>
> why not classify gestures directly?

The answer is that

different gestures produce

complex temporal sequences

of velocity spectra.

The optimization estimates

only

one snapshot.

The CNN-GRU learns

how these snapshots evolve over time.

---

# Paper

The original Widar implementation reconstructs a velocity spectrum by solving a constrained nonlinear optimization problem using `fmincon`.

The optimization minimizes the mismatch between the observed Doppler spectrum and the Doppler spectrum predicted by the forward geometric model while encouraging sparse velocity distributions.

---

# Our Interpretation

This optimization is the core innovation of Widar.

Unlike purely data-driven approaches,

the algorithm explicitly embeds electromagnetic propagation and sensing geometry into the representation.

Rather than asking a neural network to infer physical constraints from data,

those constraints are enforced analytically before learning begins.

This produces a physically meaningful intermediate representation that is both interpretable and easier to learn from.

---

# Research Notes

Studying the MATLAB implementation revealed an important conceptual insight.

The optimization does not estimate Doppler.

The STFT has already provided the Doppler spectrum.

Instead,

the optimization solves an inverse physics problem: it infers the latent velocity distribution whose forward projection best reproduces the observed Doppler measurements.

Recognizing this distinction greatly clarified the role of the `A` matrix, the `VDM` tensor, and the objective function.

---

# Beyond the Paper

This stage presents several exciting research opportunities.

1. Replace the optimization with a differentiable neural network that learns the inverse mapping from Doppler to velocity.

2. Incorporate uncertainty in the transmitter and receiver geometry instead of assuming fixed positions.

3. Predict a continuous velocity field rather than a discretized 20×20 grid.

4. Integrate the optimization into an end-to-end trainable architecture using differentiable physics.

5. Fuse the recovered velocity spectrum with geometric information from SpotFi and learned latent representations from DeepFi.

These ideas align naturally with the unified CSI + IMU architecture proposed later in this notebook, where geometry, motion, and learned representations are combined into a single perception pipeline.


# Chapter 6 Summary : End-to-End Reconstruction of Widar 3.0

---

## 6.17 The Complete Widar Pipeline

The complete Widar 3.0 pipeline reconstructed during this project is shown below.

```
                         Raw CSI
                            │
                            ▼
                 Reference Antenna Selection
                            │
                            ▼
                  Amplitude Adjustment
                            │
                            ▼
                 Conjugate Multiplication
                            │
                            ▼
                  Butterworth Filtering
                            │
                            ▼
                  Complex Principal Component Analysis
                            │
                            ▼
               Short-Time Fourier Transform (STFT)
                            │
                            ▼
                     Doppler Spectrum
                            │
                            ▼
              Doppler-to-Velocity Optimization
                            │
                            ▼
                     Velocity Spectrum
                            │
                            ▼
                      CNN Feature Extractor
                            │
                            ▼
                     GRU Temporal Encoder
                            │
                            ▼
                    Gesture Classification
```

Although this appears to be a standard signal processing pipeline,

each stage fundamentally changes the information contained within the signal.

Understanding these transformations proved to be considerably more important than simply reproducing the MATLAB implementation.

---

# 6.18 Information Flow Through the Pipeline

One of the most useful ways to understand Widar is to ask

> **What information exists before and after each processing stage?**

The following table summarizes this transformation.

| Stage | Input | Output | Information Preserved | Information Lost |
|---------|---------|---------|-----------------------|------------------|
| Raw CSI | Complex wireless channel | Complex CSI tensor | Everything measured by the NIC | None |
| Reference Selection | 90 CSI streams | Reference + dynamic streams | Stable channel estimate | Information from discarded reference candidates |
| Amplitude Adjustment | Raw amplitudes | Calibrated amplitudes | Phase | Original amplitude scale |
| Conjugate Multiplication | Two CSI streams | Relative CSI | Relative phase | Absolute phase |
| Butterworth Filter | Relative CSI | Motion signal | Human motion frequencies | Static clutter and high-frequency noise |
| Complex PCA | 60 CSI streams | One dominant component | Dominant correlated motion | Weak motion components |
| STFT | Time signal | Doppler spectrum | Time-frequency information | Exact phase evolution |
| Velocity Mapping | Doppler spectrum | Velocity spectrum | Physical motion representation | Continuous velocity distribution |
| CNN-GRU | Velocity sequence | Gesture class | Learned temporal patterns | Intermediate representation |

Several important observations emerge immediately.

---

# 6.19 Signal Processing is Progressive Compression

The Widar pipeline does not simply transform the data.

Instead,

every stage compresses the representation.

```
Raw CSI

↓

Millions of complex measurements

↓

60 CSI Streams

↓

1 Complex Signal

↓

2D Doppler Spectrum

↓

20×20 Velocity Spectrum

↓

Feature Vector

↓

Gesture Label
```

Each operation reduces the dimensionality while attempting to preserve the information most relevant for gesture recognition.

---

# 6.20 Widar is a Physics-Driven Pipeline

One of the strongest impressions gained during implementation was that Widar is fundamentally **physics-first**.

The neural network appears only at the very end.

Everything before that is derived from physical reasoning.

```
Electromagnetic Waves

↓

Propagation

↓

CSI

↓

Signal Processing

↓

Physical Representation

↓

Deep Learning
```

Rather than asking a neural network to discover physical relationships,

Widar explicitly constructs those relationships using

- propagation geometry,
- Doppler theory,
- optimization.

The neural network is responsible only for recognizing temporal patterns in the recovered velocity spectra.

---

# 6.21 Advantages of This Design

Several advantages become apparent.

### Interpretability

Every intermediate representation has a physical meaning.

```
CSI

↓

Relative Phase

↓

Motion Signal

↓

Doppler

↓

Velocity
```

Nothing inside the pipeline is a completely opaque latent feature.

---

### Data Efficiency

Since much of the physics has already been encoded,

the neural network requires fewer parameters and less training data.

---

### Generalization

Because the representation is grounded in propagation physics,

the extracted features are expected to transfer more easily across environments than purely learned features.

---

# 6.22 Limitations of This Design

During reproduction,

another observation became equally important.

Every processing stage also removes information.

For example,

Reference Selection

```
90 Streams

↓

60 Streams
```

Information from the remaining antenna combinations is discarded.

---

Complex PCA

```
60 Signals

↓

1 Signal
```

Only the dominant principal component survives.

Potentially useful secondary components disappear.

---

STFT

```
Complex Signal

↓

Magnitude Spectrum
```

The temporal phase evolution is no longer explicitly preserved.

---

Velocity Mapping

```
Continuous Motion

↓

20×20 Grid
```

The recovered motion is quantized.

Fine-grained velocity information is inevitably lost.

---

# 6.23 A New Perspective

Originally,

we viewed these operations simply as preprocessing.

After implementing each stage individually,

a different interpretation emerged.

Each operation acts as an

**information bottleneck.**

```
Raw CSI

↓

Filter

↓

Compress

↓

Approximate

↓

Discard

↓

Learn
```

Every discarded component is unavailable to later stages.

This realization became one of the key motivations for exploring alternative architectures.

---

# 6.24 Comparison with End-to-End Learning

Modern deep learning systems often follow

```
Raw CSI

↓

Large Neural Network

↓

Prediction
```

Widar instead follows

```
Raw CSI

↓

Physics

↓

Signal Processing

↓

Deep Learning
```

Neither philosophy is universally superior.

Physics-based systems provide

- interpretability,
- robustness,
- lower data requirements.

End-to-end systems provide

- flexibility,
- adaptability,
- potentially richer feature representations.

The ideal solution may lie between these two extremes.

---

# 6.25 Research Insights Obtained During This Work

Reconstructing Widar from the released MATLAB implementation led to several important insights.

### Insight 1

Most of the computational effort occurs **before** the neural network.

---

### Insight 2

The CNN-GRU never sees raw CSI.

It operates only on a highly processed velocity representation.

---

### Insight 3

Every preprocessing stage encodes assumptions about

- propagation,
- motion,
- geometry.

If these assumptions are violated,

performance may degrade.

---

### Insight 4

Several handcrafted components could potentially be replaced by learned modules,

provided that the underlying physical constraints are preserved.

---

# 6.26 Connection to SpotFi and DeepFi

At this point,

we have completely reconstructed Widar.

However,

one important question remains.

> **Is velocity the only useful representation contained within CSI?**

The answer is clearly **no**.

CSI simultaneously contains

- geometry,
- propagation delay,
- multipath,
- Doppler,
- amplitude fingerprints.

Widar extracts only the motion information.

Other algorithms focus on different aspects.

```
Raw CSI

        │

        ├──────────► SpotFi
        │             AoA
        │             ToF
        │             Multipath
        │
        ├──────────► DeepFi
        │             Fingerprints
        │             Latent Representation
        │
        └──────────► Widar
                      Doppler
                      Velocity
```

Each algorithm observes the same wireless channel,

but projects it into a different representation.

---

# 6.27 Toward a Unified CSI Representation

One of the central ideas that emerged during this project is that these representations should not compete with one another.

Instead,

they should complement one another.

Rather than selecting a single representation,

it may be preferable to preserve multiple physical views of the wireless channel simultaneously.

This observation directly motivates the architecture proposed later in this notebook.

```
                      Raw CSI
                          │
         ┌────────────────┼────────────────┐
         │                │                │
         ▼                ▼                ▼
     Geometry         Motion         Fingerprints
     (SpotFi)         (Widar)        (DeepFi)
         │                │                │
         └────────────────┼────────────────┘
                          ▼
              Unified CSI Representation
                          │
                    IMU Preintegration
                          │
               Cross-modal Feature Fusion
                          │
                    Transformer Encoder
                          │
          Localization • Mapping • Navigation
```

Rather than replacing existing methods,

this architecture attempts to preserve complementary information that is otherwise discarded by individual pipelines.

---

# Looking Ahead

The next chapter shifts focus from motion to geometry.

Where Widar reconstructs **velocity**, the next algorithm reconstructs **propagation geometry**.

This marks the transition from **Widar** to **SpotFi**, beginning with the fundamental concepts of

- antenna arrays,
- Angle of Arrival (AoA),
- Time of Flight (ToF),
- multipath separation,
- and the MUSIC algorithm.

Together,

these methods reveal a completely different view of the same CSI measurements.

