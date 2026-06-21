from __future__ import annotations

import numpy as np


class RidgeSurrogate:
    """Small dependency-light surrogate with a distance-based uncertainty proxy."""

    def __init__(self, alpha: float = 1.0):
        self.alpha = alpha
        self.coef_: np.ndarray | None = None
        self.x_mean_: np.ndarray | None = None
        self.x_std_: np.ndarray | None = None
        self.train_x_: np.ndarray | None = None
        self.residual_std_: float = 1.0

    def fit(self, x: np.ndarray, y: np.ndarray) -> "RidgeSurrogate":
        self.x_mean_ = x.mean(axis=0)
        self.x_std_ = x.std(axis=0) + 1e-9
        z = (x - self.x_mean_) / self.x_std_
        z1 = np.c_[np.ones(len(z)), z]
        reg = self.alpha * np.eye(z1.shape[1])
        reg[0, 0] = 0
        self.coef_ = np.linalg.pinv(z1.T @ z1 + reg) @ z1.T @ y
        pred = z1 @ self.coef_
        self.residual_std_ = float(np.std(y - pred) + 1e-9)
        self.train_x_ = z
        return self

    def predict(self, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        if self.coef_ is None or self.x_mean_ is None or self.x_std_ is None or self.train_x_ is None:
            raise RuntimeError("Surrogate not fitted")
        z = (x - self.x_mean_) / self.x_std_
        z1 = np.c_[np.ones(len(z)), z]
        mean = z1 @ self.coef_
        # uncertainty proxy: distance to nearest observed sample times residual scale
        distances = np.sqrt(((z[:, None, :] - self.train_x_[None, :, :]) ** 2).sum(axis=2))
        nearest = distances.min(axis=1)
        std = self.residual_std_ * (1.0 + nearest / (np.median(nearest) + 1e-9))
        return mean, std
