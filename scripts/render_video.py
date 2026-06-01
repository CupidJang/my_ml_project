"""
Render a Pendulum-v1 demo video for the presentation slides.
Uses an energy-based swing-up controller so the pendulum looks dynamic.
Output: results/figures/pendulum_demo.mp4
"""
import os, sys
import numpy as np
import gymnasium as gym
import cv2

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

FPS = 30
DURATION_SEC = 12
N_STEPS = FPS * DURATION_SEC
OUT_PATH = os.path.join("results", "figures", "pendulum_demo.mp4")


def energy_controller(cos_th, sin_th, thdot):
    """Simple energy-based swing-up (Spong's method)."""
    theta = np.arctan2(sin_th, cos_th)
    E_target = 2 * 10.0 * 1.0          # 2*m*g*l  (energy at upright)
    E_current = 0.5 * 1.0 * thdot**2 - 10.0 * 1.0 * np.cos(theta)
    k = 0.5
    torque = k * thdot * (E_current - E_target)
    return float(np.clip(torque, -2.0, 2.0))


def render_video():
    env = gym.make("Pendulum-v1", render_mode="rgb_array")
    obs, _ = env.reset(seed=7)
    cos_th, sin_th, thdot = obs

    frame0 = env.render()
    h, w = frame0.shape[:2]

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(OUT_PATH, fourcc, FPS, (w, h))

    for step in range(N_STEPS):
        torque = energy_controller(cos_th, sin_th, thdot)
        obs, _, terminated, truncated, _ = env.step(np.array([torque]))
        cos_th, sin_th, thdot = obs

        frame = env.render()               # RGB
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        # Overlay text
        theta = np.arctan2(sin_th, cos_th)
        cv2.putText(frame_bgr,
                    f"theta={np.degrees(theta):+.1f} deg  thdot={thdot:+.2f}  torque={torque:+.2f}",
                    (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1,
                    cv2.LINE_AA)
        cv2.putText(frame_bgr, f"Step {step+1}/{N_STEPS}",
                    (10, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1,
                    cv2.LINE_AA)

        writer.write(frame_bgr)

        if terminated or truncated:
            obs, _ = env.reset()
            cos_th, sin_th, thdot = obs

    writer.release()
    env.close()
    print(f"Video saved: {OUT_PATH}  ({N_STEPS} frames @ {FPS}fps)")


if __name__ == "__main__":
    render_video()
