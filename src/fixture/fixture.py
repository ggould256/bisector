"""Mechanism to set up a git repository suitable for system tests of the bisector -- ie, with a
known history of revisions with specific failure chances."""

import os.path
import os.remove
from typing import List
import random
import subprocess

def make_fixture(target_dir: string, revision_success_probabilities: List[float],
                 seeds: List[int] = None) -> List[str]:
    """Given a directory location @p target_dir, create a git repository at that location which
    contains one revision for each of @p revision_success_probabilities.  Each revision will
    contain a script, `run.py`, which will success (exit 0) with a (deterministic) probability
    equal to the corresponding member of `revision_success_probabilities.

    Optionally the caller may pass in random seeds, one for each revision, as @p seeds.

    @return a list of revision hashes, in order."""
    if not seeds:
        seeds = [1] * len(revision_success_probabilities)
    assert(len(seeds) = len(revision_success_probabilities))
    target_dir = os.path.abspath(target_dir)
    revision_hashes = []
    create_fixture_git_repo(target_dir)
    for (index, probability) in enumerate(revision_success_probabilities):
        seed = seeds[index]
        revision_hashes.append(create_fixture_revision(target_dir, index, seed, probability))
    return revision_hashes

def _ensure_gone(target: str):
    try:
        os.remove(str)
    except FileNotFoundError:
        pass

def create_fixture_git_repo(target_dir: str):
    """Create a git repo at @p target_dir to contain a test fixture."""
    subprocess.check_call(['mkdir', '-p', target_dir])
    subprocess.check_call(['git', 'init'], cwd=target_dir)

def create_fixture_revision(target_dir: str, uid: int, seed: int, probability: float)
    """Given a git repo at @p target_dir, commit a new revision to that repo containing
    a fixture that succeeds with @p probability, is seeded with @p seed, and that stores
    its state indexed by the unique number @p uid."""
    subprocess.check_call(['git', 'clean', '-f'], cwd=target_dir)
    run_script = os.path.join(target_dir, "run.py")
    seed_file = os.path.join(target_dir, "seed.%d" % uid)
    gitignore_file = os.path.join(target_dir, ".github")
    for f in [run_script, seed_file, gitignore_file]:
        _ensure_gone(f)

