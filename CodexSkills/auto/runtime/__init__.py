"""SkillOps Auto runtime safety kernel.

The package is deliberately non-active until coordinated M0c activation.  It
contains deterministic, testable primitives only; importing it performs no
filesystem, network, Git, notification, or automation mutation.
"""

from .core import AutoRuntimeError, FakeClock, SystemClock

__all__ = ["AutoRuntimeError", "FakeClock", "SystemClock"]
