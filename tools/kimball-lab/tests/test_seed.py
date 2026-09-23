"""The seed is the contract: deterministic, and it contains every planted case."""

from __future__ import annotations

import hashlib

from kimball_lab import seed


def _digest(path):
    h = hashlib.sha256()
    for f in sorted(path.rglob("*")):
        if f.is_file():
            h.update(f.relative_to(path).as_posix().encode())
            h.update(f.read_bytes())
    return h.hexdigest()


def test_same_seed_same_bytes(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    seed.write(seed.generate(seed=7, scale=1), a)
    seed.write(seed.generate(seed=7, scale=1), b)
    assert _digest(a) == _digest(b)


def test_planted_cases_exist_at_the_smallest_scale(manifest):
    p = manifest["planted"]
    assert len(p["inferred_member_accounts"]) == seed.N_INFERRED
    assert len(p["backdated_corrections"]) == seed.N_CORRECTIONS
    assert len(p["late_fees_across_segment_change"]) == seed.N_LATE_ACROSS_CHANGE
    assert len(p["segment_changes"]) >= 16
    assert len(p["joint_accounts"]) > 0
    assert p["late_facts"] > 0


def test_ground_truth_covers_every_technique(truth):
    assert sorted(truth) == [f"{n:02d}" for n in range(1, 14)]
    assert all(truth[k] for k in truth)


def test_eighteen_batches(seed_dir):
    batches = sorted(p.name for p in seed_dir.iterdir() if p.is_dir())
    assert batches == [f"batch={b}" for b in seed.BATCHES]
    assert len(batches) == 18
