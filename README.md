# Fuzzy Bisector for Git

This is a tool created to do the work of `git bisect` when you are concerned
not with an outright failing test but with a change in the frequency with
which a test fails.  It is meant to solve both the "when did this test become
flaky?" problem and the "has this always been this flaky?" problem.

THe statistical underpinnings 