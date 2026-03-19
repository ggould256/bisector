from typing import List

import numpy as np
from numpy.typing import NDArray
from scipy.stats import chi2

"""A basic mathematical model for the bisector.

The math models a probability distribution function

```
p(x | a, b, c)) = { a : x < c ;   b : x >= c }
```

a and b are probabilities of success, and c is a change point.  The bisector
logic is only valid if this assumption holds true.

This library provides maximum-likelihood estimation of a, b, and c -- that is,
it selects c that maximizes the likelihood of the data given (a, b, c), then
provides the best estimated a and b for that c.
"""


def estimate_parameters(
        inputs: List[int] | NDArray[np.int32],
        results: List[bool] | NDArray[np.bool_]
    ) -> tuple[float, float, int]:
    """
    Estimate the parameters a, b, and c using Maximum Likelihood Estimation.

    Parameters:
        inputs (list or numpy array): Positive integers representing the x of tests performed.
        results (list or numpy array): Binary outcomes (0 or 1) representing the results of the tests.

    Returns:
        a_hat (float): Estimated parameter a.
        b_hat (float): Estimated parameter b.
        c_hat (int): Estimated parameter c.
    """
    x = np.array(inputs, dtype=int)
    y = np.array(results, dtype=bool)

    assert len(x) == len(y), "Inputs x and y must have the same length"
    assert all(x > 0), "All x values must be positive"
    assert set(y).issubset({0, 1}), "All y values must be binary (0 or 1)"

    max_log_likelihood = float('-inf')
    best_a = 0.0
    best_b = 0.0
    best_c = 0

    # Iterate over possible values of c
    for c in range(1, np.max(x) + 1):
        # Split data into two groups
        group1 = y[x < c]  # x_i < c
        group2 = y[x >= c]  # x_i >= c

        # Compute a and b
        a = np.mean(group1) if len(group1) > 0 else 0.0
        b = np.mean(group2) if len(group2) > 0 else 0.0

        # Ensure probabilities are in [0, 1]
        a = np.clip(a, 0, 1)
        b = np.clip(b, 0, 1)

        # Compute log-likelihood
        log_likelihood = 0.0
        if len(group1) > 0:
            log_likelihood += np.sum(group1 * np.log(a + 1e-10) + (1 - group1) * np.log(1 - a + 1e-10))
        if len(group2) > 0:
            log_likelihood += np.sum(group2 * np.log(b + 1e-10) + (1 - group2) * np.log(1 - b + 1e-10))

        # Update best parameters if log-likelihood is improved
        if log_likelihood > max_log_likelihood:
            max_log_likelihood = log_likelihood
            best_c = c
            best_a = a
            best_b = b

    return best_a, best_b, best_c


def likelihood_ratio_test(x, y, a_hat, b_hat, c_hat):
    """
    Perform a likelihood ratio test for the null hypothesis a = b.

    Parameters:
        x (list or numpy array): Positive integers representing the input values.
        y (list or numpy array): Binary outcomes (0 or 1).
        a_hat (float): Estimated parameter a (MLE under the alternative hypothesis).
        b_hat (float): Estimated parameter b (MLE under the alternative hypothesis).
        c_hat (int): Estimated parameter c (MLE under the alternative hypothesis).

    Returns:
        p_value (float): The p-value for the test.
    """
    x = np.array(x)
    y = np.array(y)

    # Split data based on c_hat
    group1 = y[x < c_hat]  # x_i < c_hat
    group2 = y[x >= c_hat]  # x_i >= c_hat

    # Compute log-likelihood under the unrestricted model (a, b)
    log_likelihood_alt = 0.0
    if len(group1) > 0:
        log_likelihood_alt += np.sum(group1 * np.log(a_hat + 1e-10) + (1 - group1) * np.log(1 - a_hat + 1e-10))
    if len(group2) > 0:
        log_likelihood_alt += np.sum(group2 * np.log(b_hat + 1e-10) + (1 - group2) * np.log(1 - b_hat + 1e-10))

    # Compute log-likelihood under the null hypothesis (a = b)
    pooled_prob = np.mean(y)  # Combined probability under H0
    log_likelihood_null = np.sum(y * np.log(pooled_prob + 1e-10) + (1 - y) * np.log(1 - pooled_prob + 1e-10))

    # Compute the likelihood ratio statistic
    lambda_stat = -2 * (log_likelihood_null - log_likelihood_alt)

    # Compute the p-value using the chi-squared distribution
    p_value = 1 - chi2.cdf(lambda_stat, df=1)

    return p_value


def compute_likelihood(x, y, a_hat, b_hat, c_hat):
    """
    Compute the likelihood for the chosen value of c.

    Parameters:
        x (list or numpy array): Positive integers representing the input values.
        y (list or numpy array): Binary outcomes (0 or 1).
        a_hat (float): Estimated parameter a (MLE under the chosen c).
        b_hat (float): Estimated parameter b (MLE under the chosen c).
        c_hat (int): Estimated parameter c (MLE).

    Returns:
        likelihood (float): The likelihood for the chosen c.
    """
    x = np.array(x)
    y = np.array(y)

    # Split data based on c_hat
    group1 = y[x < c_hat]  # x_i < c_hat
    group2 = y[x >= c_hat]  # x_i >= c_hat

    # Compute log-likelihood
    log_likelihood = 0.0
    if len(group1) > 0:
        log_likelihood += np.sum(group1 * np.log(a_hat + 1e-10) + (1 - group1) * np.log(1 - a_hat + 1e-10))
    if len(group2) > 0:
        log_likelihood += np.sum(group2 * np.log(b_hat + 1e-10) + (1 - group2) * np.log(1 - b_hat + 1e-10))

    # Convert log-likelihood to likelihood
    likelihood = np.exp(log_likelihood)

    return likelihood
