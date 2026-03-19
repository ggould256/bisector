import unittest

from git_fuzzy_bisector.core.math import (
    compute_likelihood,
    estimate_parameters,
    likelihood_ratio_test,
)


class TestMath(unittest.TestCase):
    X_SAMPLES = [    1,     2,     3,     4,     5,     6,     7]
    Y_SAMPLES = [False, False, False,  True,  True,  True,  True]

    def test_estimate_parameters(self):
        """Test that the parameter estimation procedure returns the correct parameters on a simple example."""
        a_hat, b_hat, c_hat = estimate_parameters(self.X_SAMPLES, self.Y_SAMPLES)
        self.assertAlmostEqual(a_hat, 0.0, delta=1e-10)  # All failures in group 1
        self.assertAlmostEqual(b_hat, 1.0, delta=1e-10)  # All successes in group 2
        self.assertEqual(c_hat, 4)          # Optimal split is between 3 and 4

    def test_likelihood_ratio_test(self):
        """Test that the likelihood ratio test returns a low p-value when the null hypothesis is false."""
        a_hat, b_hat, c_hat = estimate_parameters(self.X_SAMPLES, self.Y_SAMPLES)
        p_val = likelihood_ratio_test(self.X_SAMPLES, self.Y_SAMPLES, a_hat, b_hat, c_hat)
        self.assertLess(p_val, 0.05)  # Expect to reject null hypothesis

    def test_compute_likelihood(self):
        """Test that the likelihood computation returns a reasonable value."""
        a_hat, b_hat, c_hat = estimate_parameters(self.X_SAMPLES, self.Y_SAMPLES)
        likelihood = compute_likelihood(self.X_SAMPLES, self.Y_SAMPLES, a_hat, b_hat, c_hat)
        self.assertGreater(likelihood, -10)  # Log-likelihood should not be too low
