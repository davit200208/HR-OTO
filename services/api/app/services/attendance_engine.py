from dataclasses import dataclass
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class AttendanceCalculation:
    worked_minutes: int
    late_minutes: int
    early_leave_minutes: int
    overtime_minutes: int
    night_minutes: int


def _local(dt: datetime, timezone: str) -> datetime:
    return dt.astimezone(ZoneInfo(timezone))


def calculate_attendance(clock_in: datetime, clock_out: datetime, scheduled_start: time | None,
                         scheduled_end: time | None, timezone: str = "Asia/Tbilisi") -> AttendanceCalculation:
    if clock_out <= clock_in:
        raise ValueError("clock_out must be after clock_in")
    start, end = _local(clock_in, timezone), _local(clock_out, timezone)
    worked = int((end - start).total_seconds() // 60)
    scheduled_start_dt = start.replace(hour=scheduled_start.hour, minute=scheduled_start.minute, second=0, microsecond=0) if scheduled_start else start
    late = max(0, int((start - scheduled_start_dt).total_seconds() // 60)) if scheduled_start else 0
    scheduled_end_dt = start.replace(hour=scheduled_end.hour, minute=scheduled_end.minute, second=0, microsecond=0) if scheduled_end else end
    if scheduled_end and scheduled_start and scheduled_end <= scheduled_start: scheduled_end_dt += timedelta(days=1)
    early = max(0, int((scheduled_end_dt - end).total_seconds() // 60)) if scheduled_end else 0
    overtime = max(0, int((end - scheduled_end_dt).total_seconds() // 60)) if scheduled_end else 0
    night = 0
    cursor = start
    while cursor < end:
        nxt = min(end, cursor + timedelta(minutes=1))
        if cursor.hour >= 22 or cursor.hour < 6: night += 1
        cursor = nxt
    return AttendanceCalculation(worked, late, early, overtime, night)


def active_break_count(breaks: list[object]) -> int:
    return sum(1 for item in breaks if getattr(item, "active", False))
