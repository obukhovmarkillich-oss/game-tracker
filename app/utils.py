def minutes_to_hours(minutes: int) -> float:
    return round(minutes / 60, 1)


def format_playtime(minutes: int) -> str:
    hours = minutes // 60
    mins = minutes % 60
    if hours == 0:
        return f"{mins} мин."
    if mins == 0:
        return f"{hours} ч."
    return f"{hours} ч. {mins} мин."
