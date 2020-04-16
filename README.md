# Fuzzy Bisector for Git

This is a tool created to do the work of `git bisect` when you are concerned
not with an outright failing test but with a change in the frequency with
which a test fails.  It is meant to solve both the "when did this test become
flaky?" problem and the "has this always been this flaky?" problem.

THe statistical underpinnings of this are tedious but not complicated.  I will
explain them in a later commit.

## Status

This project is a work in progress.  I toss in an hour or two when I feel like
it.

The project's commit history is a mess.  I'll probably punch the history
eraser button some time soon just to clean up all the times I accidentally
pushed with the wrong ssh key.
