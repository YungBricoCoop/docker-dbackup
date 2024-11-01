from typing import List


def split_and_trim(s: str, sep: str = ",") -> List[str]:
    if not s:
        return []
    if sep not in s:
        return [s.strip()]
    return [x.strip() for x in s.split(sep) if x.strip()]
