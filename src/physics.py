"""
Theoretical physics for the Gymnasium Pendulum-v1 environment.

Pendulum dynamics (from Gymnasium source):
    theta'' = (3g / 2l) * sin(theta) + (3 / (m * l^2)) * torque
with g=10.0, m=1.0, l=1.0  =>  theta'' = 15*sin(theta) + 3*torque

Gymnasium uses Euler integration with dt=0.05 and clips theta_dot to [-8, 8].
We implement both Euler and RK4 to expose the integration error as a
learnable signal.
"""

import numpy as np

# Pendulum physical constants (match Gymnasium defaults)
G = 10.0
M = 1.0
L = 1.0
DT = 0.05
MAX_SPEED = 8.0
MAX_TORQUE = 2.0


def _pendulum_accel(theta: float, theta_dot: float, torque: float) -> float:
    """Angular acceleration from the pendulum ODE."""
    return (3 * G / (2 * L)) * np.sin(theta) + (3.0 / (M * L**2)) * torque


def euler_step(theta: float, theta_dot: float, torque: float) -> tuple[float, float]:
    """
    One step of Euler integration — identical to Gymnasium's internal update.
    Returns (theta_new, theta_dot_new).
    """
    torque = np.clip(torque, -MAX_TORQUE, MAX_TORQUE)
    accel = _pendulum_accel(theta, theta_dot, torque)
    theta_dot_new = np.clip(theta_dot + accel * DT, -MAX_SPEED, MAX_SPEED)
    theta_new = theta + theta_dot_new * DT
    return theta_new, theta_dot_new


def rk4_step(theta: float, theta_dot: float, torque: float,
             n_substeps: int = 20) -> tuple[float, float]:
    """
    RK4 integration over [0, DT] using n_substeps sub-intervals.
    Treated as the 'ground-truth' physics for error estimation.
    theta_dot is clipped only at the end to match environment semantics.
    """
    torque = np.clip(torque, -MAX_TORQUE, MAX_TORQUE)
    h = DT / n_substeps
    th, thdot = theta, theta_dot

    for _ in range(n_substeps):
        def deriv(th_, thdot_):
            return thdot_, _pendulum_accel(th_, thdot_, torque)

        k1_th, k1_thdot = deriv(th, thdot)
        k2_th, k2_thdot = deriv(th + h/2 * k1_th, thdot + h/2 * k1_thdot)
        k3_th, k3_thdot = deriv(th + h/2 * k2_th, thdot + h/2 * k2_thdot)
        k4_th, k4_thdot = deriv(th + h * k3_th, thdot + h * k3_thdot)

        th    = th    + (h / 6) * (k1_th    + 2*k2_th    + 2*k3_th    + k4_th)
        thdot = thdot + (h / 6) * (k1_thdot + 2*k2_thdot + 2*k3_thdot + k4_thdot)

    thdot = np.clip(thdot, -MAX_SPEED, MAX_SPEED)
    return th, thdot


def integration_error(theta: float, theta_dot: float,
                      torque: float) -> tuple[float, float]:
    """
    Returns (err_theta, err_theta_dot) = Euler_result - RK4_result.
    This is the target label for the ML models.
    """
    th_e, thdot_e = euler_step(theta, theta_dot, torque)
    th_r, thdot_r = rk4_step(theta, theta_dot, torque)
    return th_e - th_r, thdot_e - thdot_r
