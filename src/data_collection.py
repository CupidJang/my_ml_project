"""
Collect trajectory data from Gymnasium Pendulum-v1.

For each (state, action) pair we record:
  - cos(theta), sin(theta), theta_dot  (the Gym observation)
  - theta, theta_dot                   (recovered from the observation)
  - torque                             (the applied action)
  - err_theta, err_theta_dot           (Euler - RK4 integration error)

The dataset is saved to data/raw/pendulum_data.npz and
data/processed/features.npy / labels.npy.
"""

import numpy as np
import gymnasium as gym
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.physics import integration_error


def collect(n_episodes: int = 500, max_steps: int = 200,
            seed: int = 42, save_dir: str = "data") -> dict:
    env = gym.make("Pendulum-v1")
    rng = np.random.default_rng(seed)

    records = []

    for ep in range(n_episodes):
        obs, _ = env.reset(seed=int(rng.integers(0, 100_000)))
        cos_th, sin_th, thdot = obs

        for _ in range(max_steps):
            # Random action (uniform exploration)
            torque = rng.uniform(-2.0, 2.0)
            action = np.array([torque], dtype=np.float32)

            # Recover theta from observation
            theta = np.arctan2(sin_th, cos_th)

            # Compute integration error before stepping
            err_th, err_thdot = integration_error(theta, thdot, torque)

            next_obs, _, terminated, truncated, _ = env.step(action)
            cos_th_n, sin_th_n, thdot_n = next_obs

            records.append([
                cos_th, sin_th, thdot, torque,   # features (4)
                theta,                            # recovered angle
                err_th, err_thdot,                # labels (2)
            ])

            cos_th, sin_th, thdot = cos_th_n, sin_th_n, thdot_n
            if terminated or truncated:
                break

        if (ep + 1) % 100 == 0:
            print(f"  Episode {ep+1}/{n_episodes} - {len(records)} samples so far")

    env.close()

    data = np.array(records, dtype=np.float64)
    X = data[:, :4]                  # [cos_th, sin_th, thdot, torque]
    y = data[:, 5:7]                 # [err_theta, err_theta_dot]
    meta = data[:, 4]                # recovered theta (for analysis)

    os.makedirs(os.path.join(save_dir, "raw"), exist_ok=True)
    os.makedirs(os.path.join(save_dir, "processed"), exist_ok=True)

    np.savez(os.path.join(save_dir, "raw", "pendulum_data.npz"),
             X=X, y=y, theta=meta)
    np.save(os.path.join(save_dir, "processed", "features.npy"), X)
    np.save(os.path.join(save_dir, "processed", "labels.npy"), y)

    print(f"\nSaved {len(X)} samples.")
    print(f"  X shape : {X.shape}  (cos_th, sin_th, thdot, torque)")
    print(f"  y shape : {y.shape}  (err_theta, err_theta_dot)")

    return {"X": X, "y": y, "theta": meta}


if __name__ == "__main__":
    collect(n_episodes=500, save_dir="data")
