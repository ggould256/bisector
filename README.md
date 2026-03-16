# Fuzzy Bisector for Git

A conventional bisector, such as `git bisect`, searches a range of versions
to find where a test went from passing to failing.  This is famously achieved
by recursively testing the version half way between the last known good and
first known good revision.

However a more common problem in modern codebases is that a test that used to
usually pass now more often fails.  A conventional bisect approach struggles
to answer this question.

This is a tool created to do the work of `git bisect` when you are concerned
not with an outright failing test but with a change in the frequency with
which a test fails.  It is meant to solve both the "when did this test become
flaky?" problem and the "has this always been this flaky?" problem.

The statistical underpinnings of this are tedious.

## Statistics

It is tempting to use a simple binonial test computing the p-value that
results prior to a revision and those subsequent are drawn from the same
distribution; this can then be normalized across all the revisions via
Bayes' theorem to obtain a p-value for the choice of revision.

That doesn't work, because the null hypothesis is wrong in _every_ revision,
so the application of Bayes' theorem is unsound -- we cannot condition the
probability on there being only one revision that falsifies the null
hypothesis.

For the sake of terminology, let's imagine we have versions `A..Z`, and
the correct answer is that change `J->K` is the right one. 

What we know:
 * A:  There are two distributions, P_A_actual and P_Z_actual.
 * B:  All version samples are drawn from one of these two distributions.
 * C:  Versions fall into two contiguous segments divided by change JK_actual.
 * D:  P_A_actual and P_Z_actual are different.

We're never going to know a P_actual, or even a prior distribution over a
P_actual, which is why a Monte Carlo approach won't work.

So all we can ask about is the probability that things are from the same
distribution.

So:  What is the probability that J is from the same distribution as A
through I?  Fisher's Exact Test is the obvious choice here.  Likewise that K
is from the same distribution as L through Z.

(There will be some empty sets invovled.  Fisher's Exact Test allows this.)

For a given JK to be accepted, we compute three p values:
 * J same distribution as AI  exact(J, AI);  correct JK must ACCEPT
 * K same distribution as LZ  exact(K, LZ);  correct JK must ACCEPT
 * AJ not equal to KZ         exact(AJ, KZ); correct JK must REJECT

To accept JK, we must accept the first two hypotheses and reject the third.
Combining accept and reject p values is not trivial, so we have some more
work to do.

For each JK, we combine (using Fisher's Method) the accept values.  We know
that this combined value can be correctly accepted for only one value, and
so we can normalize this statistic to sum to 1 over the whole list.  We call
this statistic ACCEPT_CHANGE.

We can make no such normalization assumption for the third value:  This
hypothesis must actually be false for all JK.  Rather, the third value
just gates whether we can accept that the analysis has enough statistical
power to reach any conclusion at all.  We call this statistic
REJECT_NULL.

Our guess is G = maxidx(ACCEPT_CHANGE), and we guess it with confidence
REJECT_NULL(G).

## Strategies

Choosing which version to test next to minimize p(Ĝ|X), given that switching
test versions may be costly, is a difficult problem.

[ More content here soon once I have a decent answer. ]


## Status

This project is a work in progress.  I toss in an hour or two when I feel like
it.

The project's commit history is a mess.  I'll probably punch the history
eraser button some time soon just to clean up all the times I accidentally
pushed with the wrong ssh key.
