"""Sydney schedule semantics shared by MANUAL and SCHEDULED triggers."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Mapping, Optional
from zoneinfo import ZoneInfo

from .core import AutoRuntimeError, require_utc


SYDNEY = ZoneInfo("Australia/Sydney")


@dataclass(frozen=True)
class RunCadence:
    trigger_kind: str
    local_date: dt.date
    forced_full: bool
    late_rejected: bool = False


class SchedulePolicy:
    timezone = "Australia/Sydney"
    local_hour = 4
    local_minute = 15

    def validate_trusted_policy(self, policy: Mapping[str, object]) -> None:
        if (
            policy.get("timezone") != self.timezone
            or policy.get("daily_schedule_local") != "04:15"
            or policy.get("sunday_forced_full") is not True
            or policy.get("late_start_rejected") is not False
            or policy.get("manual_uses_same_orchestrator") is not True
        ):
            raise AutoRuntimeError("SCHEDULE_POLICY_CONTRACT_MISMATCH")

    def classify(
        self,
        trigger_kind: str,
        now_utc: dt.datetime,
        *,
        last_full_local_date: Optional[dt.date],
    ) -> RunCadence:
        if trigger_kind not in {"MANUAL", "SCHEDULED"}:
            raise AutoRuntimeError("TRIGGER_KIND_INVALID")
        local = require_utc(now_utc).astimezone(SYDNEY)
        most_recent_sunday = local.date() - dt.timedelta(days=(local.weekday() + 1) % 7)
        overdue = last_full_local_date is None or last_full_local_date < most_recent_sunday
        forced = local.weekday() == 6 or overdue
        return RunCadence(trigger_kind, local.date(), forced, False)

    def scheduled_instant(self, local_date: dt.date) -> dt.datetime:
        local = dt.datetime(
            local_date.year,
            local_date.month,
            local_date.day,
            self.local_hour,
            self.local_minute,
            tzinfo=SYDNEY,
        )
        return local.astimezone(dt.timezone.utc)

    def next_scheduled_after(self, now_utc: dt.datetime) -> dt.datetime:
        current = require_utc(now_utc)
        local = current.astimezone(SYDNEY)
        candidate = self.scheduled_instant(local.date())
        if candidate <= current:
            candidate = self.scheduled_instant(local.date() + dt.timedelta(days=1))
        return candidate
