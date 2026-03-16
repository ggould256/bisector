# Implementation notes

Starting with p-value statistics is a trap here.  The symmetries of the
problem require combination of p-values, and p-values cannot be combined
without quantifying independence; to quantify independence of individual
versions from arms of the distribution requires a prior about possible
probabilities, and that means that we are doing likelihood statistics.

Rather, we have a set of discrete hypotheses θ1, .. θn, we have a pair of
continuous variables B and A, and we observe a sample of outcomes X.  We
want to know L(θi | x).

Our first decision must be on a plausible A and B to test.  A and B are
nuisance parameters in this analysis and so should be estimated from data
as early as possible to simplify the remainder of the analysis.  We can
estimate A and B simply by choosing that of the θ that minimizes the p value
of a Fisher test.  Of course that stacks the decks a bit toward that θ, but
that is in effect a simple degrees-of-freedom reduction and should only
really affect the scale of our result.  Moreover if we had infinite samples
the correct θ would have the best Fisher p anyway, so there's a convergence
lemma to be had in here somewhere.ha

Once we have A, B then we can perform P(x | θi, A, B) -> L(θi | x, A, B).
