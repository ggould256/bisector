#!/usr/bin/env python3
"""Mechanism to set up a git repository suitable for system tests of the bisector -- ie, with a
known history of revisions with specific failure chances."""

import os.path
import os
from typing import List
import random
import stat
import subprocess
import textwrap

def make_fixture(target_dir: str, revision_success_probabilities: List[float], quiet: bool) -> List[str]:
    """Given a directory location @p target_dir, create a git repository at that location which
    contains one revision for each of @p revision_success_probabilities.  Each revision will
    contain a script, `run.py`, which will succeed (exit 0) with a (deterministic) probability
    equal to the corresponding member of `revision_success_probabilities.

    @return a list of revision hashes, in order.
    """
    target_dir = os.path.abspath(target_dir)
    os.makedirs(target_dir)
    revision_hashes = []
    create_fixture_git_repo(target_dir, quiet)
    for (index, probability) in enumerate(revision_success_probabilities):
        revision_hashes.append(create_fixture_revision(target_dir, index, probability, quiet))
    return revision_hashes

def _ensure_gone(target: str):
    try:
        os.remove(target)
    except FileNotFoundError:
        pass

def create_fixture_git_repo(target_dir: str, quiet:bool):
    """Create a git repo at @p target_dir to contain a test fixture."""
    quiet_args = {"stdout": subprocess.DEVNULL} if quiet else {}
    subprocess.check_call(['mkdir', '-p', target_dir], **quiet_args)
    subprocess.check_call(['git', 'init'], cwd=target_dir, **quiet_args)

def create_fixture_revision(target_dir: str, uid: int, probability: float, quiet: bool):
    """Given a git repo at @p target_dir, commit a new revision to that repo containing
    a fixture that succeeds with @p probability, is seeded with @p seed, and that stores
    its state indexed by the unique number @p uid."""
    quiet_args = {"stdout": subprocess.DEVNULL} if quiet else {}
    subprocess.check_call(['git', 'clean', '-f'], cwd=target_dir, **quiet_args)

    gitignore_file = os.path.join(target_dir, ".gitignore")
    _create_gitignore_file(gitignore_file)
    subprocess.check_call(['git', 'add', gitignore_file], cwd=target_dir, **quiet_args)

    seed_file = os.path.join(target_dir, "seed.%d" % uid)
    run_script = os.path.join(target_dir, "run.py")
    _create_run_script(run_script, uid, seed_file, probability)
    subprocess.check_call(['git', 'add', run_script], cwd=target_dir, **quiet_args)

    subprocess.check_call(['git', 'commit', '-m', "revision id %d" % uid], cwd=target_dir, **quiet_args)
    revision = subprocess.check_output(['git', 'log', "--pretty=%H", '--max-count=1'], cwd=target_dir).rstrip()
    if not quiet:
        print("Created revision %d, hash %s, with probability %f" % (uid, revision, probability))
    return revision

def _create_gitignore_file(target_path: str):
    _ensure_gone(target_path)
    with open(target_path, "w") as f:
        f.write(textwrap.dedent("""\
            /seed.*
            """))

def _create_run_script(target_path: str, uid: int, seed_file: str, probability: float):
    _ensure_gone(target_path)
    with open(target_path, "w") as f:
        f.write(textwrap.dedent("""\
            #!/usr/bin/env python3
            import pickle
            import random
            import sys
            rnd = random.Random()
            if __name__ == "__main__":
                try:
                    with open("{seedfile}", "rb") as f:
                        rnd.setstate(pickle.load(f))
                except FileNotFoundError:
                    rnd.seed({uid})
                sample = rnd.random()
                succeed = sample < {probability}
                print("sample", sample, "vs", {probability}, ":", succeed)
                with open("{seedfile}", "wb") as f:
                    pickle.dump(rnd.getstate(), f)
                sys.exit(0 if succeed else 1)
            """.format(seedfile=seed_file, uid=uid, probability=probability)))
    os.chmod(target_path, stat.S_IRWXU)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("dirname", type=str, help="Directory in which to create the fixture")
    parser.add_argument("--num-revs", type=int, default=10, help="Number of revisions to create")
    parser.add_argument("--initial-prob", type=float, default=1., help="Probability of success before the critical revision")
    parser.add_argument("--before-revs", type=int, default=5, help="Number of revisions before probability changes")
    parser.add_argument("--final-prob", type=float, default=0., help="Probability of success after the critical revision")
    parser.add_argument("--quiet", action="store_true", help="Suppress all stdout output except revision list")

    options = parser.parse_args()
    assert(options.num_revs > 1)
    assert(options.before_revs < options.num_revs)
    rev_probs = ([options.initial_prob] * options.before_revs +
        [options.final_prob] * (options.num_revs - options.before_revs))
    revisions = make_fixture(options.dirname, rev_probs, options.quiet)
    for r in revisions:
        print(str(r, encoding="utf-8"))
