# -*- coding: utf-8 -*-
"""CART regression tree and stochastic gradient boosting regressor written from scratch (NumPy only).

The implementation is deliberately small and easy to inspect and does not depend on scikit-learn.
It also provides ordinary least squares and the RMSE, MAE and R2 metrics.
"""
import numpy as np


class _Node:
    __slots__ = ("feature", "threshold", "left", "right", "value", "n", "is_leaf")

    def __init__(self):
        self.feature = None
        self.threshold = None
        self.left = None
        self.right = None
        self.value = 0.0
        self.n = 0
        self.is_leaf = True


class RegressionTree:
    """A small CART regression tree (SSE-minimizing splits, exhaustive threshold search)."""

    def __init__(self, max_depth=3, min_samples_leaf=5, min_samples_split=10):
        self.max_depth = max_depth
        self.min_samples_leaf = min_samples_leaf
        self.min_samples_split = min_samples_split
        self.root = None
        self.n_features_ = 0
        self.feature_importances_ = None

    def fit(self, X, y, sample_weight=None):
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)
        n, p = X.shape
        self.n_features_ = p
        self._importance = np.zeros(p)
        if sample_weight is None:
            sample_weight = np.ones(n)
        self.root = self._build(X, y, sample_weight, depth=0)
        total = self._importance.sum()
        self.feature_importances_ = self._importance / total if total > 0 else self._importance
        return self

    def _sse(self, y, w):
        if len(y) == 0:
            return 0.0
        m = np.average(y, weights=w)
        return np.sum(w * (y - m) ** 2)

    def _build(self, X, y, w, depth):
        node = _Node()
        node.n = len(y)
        node.value = float(np.average(y, weights=w)) if node.n else 0.0
        if depth >= self.max_depth or node.n < self.min_samples_split or node.n <= 2 * self.min_samples_leaf:
            return node
        parent_sse = self._sse(y, w)
        if parent_sse <= 1e-12:
            return node

        best_gain, best_feat, best_thr = 0.0, None, None
        n, p = X.shape
        for f in range(p):
            col = X[:, f]
            order = np.argsort(col)
            col_sorted = col[order]
            uniq = np.unique(col_sorted)
            if len(uniq) < 2:
                continue
            thresholds = (uniq[:-1] + uniq[1:]) / 2.0
            # limit number of candidate thresholds for speed on continuous features
            if len(thresholds) > 40:
                idxs = np.linspace(0, len(thresholds) - 1, 40).astype(int)
                thresholds = thresholds[idxs]
            for thr in thresholds:
                left_mask = col <= thr
                n_left = left_mask.sum()
                n_right = n - n_left
                if n_left < self.min_samples_leaf or n_right < self.min_samples_leaf:
                    continue
                sse_l = self._sse(y[left_mask], w[left_mask])
                sse_r = self._sse(y[~left_mask], w[~left_mask])
                gain = parent_sse - (sse_l + sse_r)
                if gain > best_gain:
                    best_gain, best_feat, best_thr = gain, f, thr

        if best_feat is None or best_gain <= 1e-9:
            return node

        node.is_leaf = False
        node.feature = best_feat
        node.threshold = best_thr
        self._importance[best_feat] += best_gain
        left_mask = X[:, best_feat] <= best_thr
        node.left = self._build(X[left_mask], y[left_mask], w[left_mask], depth + 1)
        node.right = self._build(X[~left_mask], y[~left_mask], w[~left_mask], depth + 1)
        return node

    def _predict_row(self, node, row):
        while not node.is_leaf:
            if row[node.feature] <= node.threshold:
                node = node.left
            else:
                node = node.right
        return node.value

    def predict(self, X):
        X = np.asarray(X, dtype=float)
        return np.array([self._predict_row(self.root, row) for row in X])


class GradientBoostingRegressor:
    """Stochastic gradient boosting for squared-error loss (Friedman, 2001/2002),
    implemented with the RegressionTree above as the weak learner.
    """

    def __init__(self, n_estimators=150, learning_rate=0.05, max_depth=3,
                 min_samples_leaf=5, subsample=0.8, random_state=42, val_fraction=0.0,
                 n_iter_no_change=None):
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.max_depth = max_depth
        self.min_samples_leaf = min_samples_leaf
        self.subsample = subsample
        self.random_state = random_state
        self.val_fraction = val_fraction
        self.n_iter_no_change = n_iter_no_change
        self.trees_ = []
        self.init_ = 0.0
        self.train_loss_ = []
        self.val_loss_ = []
        self.best_n_estimators_ = n_estimators
        self.feature_importances_ = None

    def fit(self, X, y, X_val=None, y_val=None):
        rng = np.random.RandomState(self.random_state)
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)
        n, p = X.shape
        self.init_ = float(np.mean(y))
        F = np.full(n, self.init_)
        F_val = None
        if X_val is not None:
            X_val = np.asarray(X_val, dtype=float)
            y_val = np.asarray(y_val, dtype=float)
            F_val = np.full(len(y_val), self.init_)

        importances = np.zeros(p)
        best_val = np.inf
        best_m = self.n_estimators
        no_improve = 0

        for m in range(self.n_estimators):
            residual = y - F
            if self.subsample < 1.0:
                idx = rng.choice(n, size=max(2, int(n * self.subsample)), replace=False)
            else:
                idx = np.arange(n)
            tree = RegressionTree(max_depth=self.max_depth, min_samples_leaf=self.min_samples_leaf)
            tree.fit(X[idx], residual[idx])
            update = tree.predict(X)
            F = F + self.learning_rate * update
            self.trees_.append(tree)
            importances += tree.feature_importances_ * (tree.feature_importances_.sum() > 0)

            self.train_loss_.append(float(np.mean((y - F) ** 2)))
            if X_val is not None:
                F_val = F_val + self.learning_rate * tree.predict(X_val)
                vloss = float(np.mean((y_val - F_val) ** 2))
                self.val_loss_.append(vloss)
                if vloss < best_val - 1e-9:
                    best_val = vloss
                    best_m = m + 1
                    no_improve = 0
                else:
                    no_improve += 1
                if self.n_iter_no_change and no_improve >= self.n_iter_no_change:
                    break

        self.best_n_estimators_ = best_m if X_val is not None else self.n_estimators
        total = importances.sum()
        self.feature_importances_ = importances / total if total > 0 else importances
        return self

    def predict(self, X, n_estimators=None):
        X = np.asarray(X, dtype=float)
        m = n_estimators if n_estimators is not None else self.best_n_estimators_
        F = np.full(X.shape[0], self.init_)
        for tree in self.trees_[:m]:
            F = F + self.learning_rate * tree.predict(X)
        return F


def rmse(y_true, y_pred):
    y_true, y_pred = np.asarray(y_true, dtype=float), np.asarray(y_pred, dtype=float)
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def mae(y_true, y_pred):
    y_true, y_pred = np.asarray(y_true, dtype=float), np.asarray(y_pred, dtype=float)
    return float(np.mean(np.abs(y_true - y_pred)))


def r2(y_true, y_pred):
    y_true, y_pred = np.asarray(y_true, dtype=float), np.asarray(y_pred, dtype=float)
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    if ss_tot <= 1e-12:
        return float("nan")
    return float(1 - ss_res / ss_tot)


def ols_fit(X, y):
    """Plain least-squares linear regression via numpy (adds intercept column)."""
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    Xb = np.hstack([np.ones((X.shape[0], 1)), X])
    coef, *_ = np.linalg.lstsq(Xb, y, rcond=None)
    return coef


def ols_predict(X, coef):
    X = np.asarray(X, dtype=float)
    Xb = np.hstack([np.ones((X.shape[0], 1)), X])
    return Xb @ coef


if __name__ == "__main__":
    # quick self-test
    rng = np.random.RandomState(0)
    X = rng.rand(200, 3) * 10
    y = np.sin(X[:, 0]) * 5 + X[:, 1] * 0.5 + rng.randn(200) * 0.3
    Xtr, Xte, ytr, yte = X[:150], X[150:], y[:150], y[150:]
    gbm = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, max_depth=3)
    gbm.fit(Xtr, ytr)
    pred = gbm.predict(Xte)
    print("self-test RMSE:", rmse(yte, pred), "R2:", r2(yte, pred))
