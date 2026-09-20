"""Real acceptance tests for smoke-two-sum. `import solution` must work."""
import solution


def _check(nums, target, expect):
    got = solution.two_sum(nums, target)
    assert isinstance(got, (list, tuple)) and len(got) == 2, f"bad shape: {got!r}"
    i, j = got
    assert i != j, "indices must differ"
    assert nums[i] + nums[j] == target, f"{got} does not sum to {target}"
    assert sorted(got) == sorted(expect)


def test_example():
    _check([2, 7, 11, 15], 9, [0, 1])


def test_negatives():
    _check([-3, 4, 3, 90], 0, [0, 2])


def test_duplicate_values():
    _check([3, 3], 6, [0, 1])


def test_late_pair():
    _check([1, 2, 3, 4, 5], 9, [3, 4])


def test_large_input():
    nums = list(range(10000))
    _check(nums, 19997, [9998, 9999])
