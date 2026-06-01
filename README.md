# Physics Error Estimation in Robot Simulation via Machine Learning

> ML Term Project — Estimating Numerical Integration Error in Gymnasium Pendulum-v1

## Problem Statement

Robot simulation environments (like those in Gymnasium) use discrete-time numerical integration to approximate continuous physics.
The most common method — **Euler integration** — is fast but introduces a systematic error compared to more accurate solvers.

This project trains ML models to **predict the integration error** (Euler vs RK4) from the current state and action of a pendulum,
with the long-term goal of error compensation in sim-to-real transfer.

### Target Variables

| Variable | Description |
|----------|-------------|
| `err_theta` | Angle error: `theta_euler - theta_rk4` |
| `err_theta_dot` | Angular velocity error: `theta_dot_euler - theta_dot_rk4` |

### Input Features

| Feature | Description |
|---------|-------------|
| `cos(theta)` | Cosine of pendulum angle |
| `sin(theta)` | Sine of pendulum angle |
| `theta_dot` | Angular velocity |
| `torque` | Applied torque action |

## Pendulum Physics

The Gymnasium `Pendulum-v1` dynamics:

```
theta'' = (3g / 2l) sin(theta) + (3 / ml^2) * torque
```

with `g=10, m=1, l=1, dt=0.05`.

- **Gym** uses **Euler integration**: `theta_dot += theta'' * dt`, `theta += theta_dot * dt`
- **Ground truth** uses **RK4** with 20 substeps over the same `dt=0.05`

## Results

| Model | err_theta R2 | err_theta_dot R2 | Mean RMSE |
|-------|-------------|-----------------|----------|
| Linear Regression (baseline) | 0.9936 | 0.5189 | 0.0172 |
| **MLP** | **0.9993** | **0.9974** | **0.0014** |

The MLP achieves near-perfect prediction of the integration error (R2 > 0.99 for both targets),
demonstrating that the Euler integration error is a smooth, learnable function of the system state.
Linear Regression captures the angle error well (linear in `theta_dot`), but fails for `theta_dot` error
due to its nonlinear dependence on `sin(theta)`.

## Project Structure

```
ML_project/
├── src/
│   ├── physics.py          # Euler & RK4 integration, error computation
│   ├── data_collection.py  # Gymnasium data collection
│   ├── models.py           # LinearRegressionModel, MLPModel
│   └── evaluate.py         # Metrics and plotting utilities
├── train_and_evaluate.py   # Main pipeline script
├── data/
│   ├── raw/                # Raw .npz file (gitignored)
│   └── processed/          # Feature/label .npy files (gitignored)
├── results/
│   ├── figures/            # Generated plots
│   ├── models/             # Saved model weights (gitignored)
│   └── metrics.json        # Evaluation metrics
├── requirements.txt
└── README.md
```

## Quickstart

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the full pipeline

```bash
python train_and_evaluate.py
```

This will:
1. Collect 100,000 samples from `Pendulum-v1` (500 episodes x 200 steps)
2. Train Linear Regression and MLP
3. Evaluate on a held-out test set (15%)
4. Save figures to `results/figures/` and metrics to `results/metrics.json`

## Environment

- Python 3.12
- Gymnasium 1.3.0
- PyTorch 2.x (CPU)
- scikit-learn 1.5

## Use of Generative AI

Claude (claude-sonnet-4-6) was used to assist with code scaffolding, project structure,
and writing boilerplate utilities. All scientific decisions (problem definition, physics derivation,
model architecture selection) were made by the project author.
