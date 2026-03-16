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

Consider your code as a random function of one variable and three parameters:
 * `f(x | a, b, c) = y` ;
   * `a` is the probability of success before the guilty change,
   * `b` is the probability of success after the guilty change,
   * `c` is the number of the first version subsequent to the guilty change,
   * `x` is the version being tested, and
   * `y` is the outcome of the test.
 * f(x) = 
   * if `x < c`:
     * `y = 1` with probability `a` 
     * `y = 0` with probability `1 - a` 
   * if `x >= c`:
     * `y = 1` with probability `b` 
     * `y = 0` with probability `1 - b` 



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
