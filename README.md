# Fuzzy Bisector for Git

This is a tool created to do the work of `git bisect` when you are concerned
not with an outright failing test but with a change in the frequency with
which a test fails.  It is meant to solve both the "when did this test become
flaky?" problem and the "has this always been this flaky?" problem.

The statistical underpinnings of this are tedious but not complicated.

## Statistics

Note:  The statistical argument below is extremely sketchy, and will not stand
up to scrutiny.  It is conservative in practice.

There is a single variable of interest, the change in which the probability
of success changed (the "guilty change", here G).

 * G designates a suspect change.
 * Ĝ designates our guess of the guilty change.
 * G* designates the true guilty change, unknown to us.
 * Pa* designates the probability of success of versions prior to G*.
 * Pb* designates the probability of success of versions subsequent to G*.

Given a set of success/failure observations about various versions, and a
hypothesis of the suspect change Ĝ, we can compute a p value as to whether
the observations falsify the hypothesis by summing the successes and failures
prior to and subsequent to Ĝ and performing a binomial test (if the numbers
were huge, we'd use Chi squared, but we expect them to be small so we can be
exact).

We can compute this for every G.  The p values will not sum to 1 of course --
each is conditional on Ĝ==G and so in that sense overconfident.  Using Bayes'
Theorem we can invert the condition so that it's p(G|X) rather than p(X|G)
if we knew a prior, but we don't have to:  p(G|X) must sum to 1
_ex hypothesi_, because we assumed going in that G* exists.

So we just normalize the sum to get p(G|X) for each G.

We iterate until some Ĝ==G|(p(G|X) < 0.05) or whatever threshold we choose.


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
