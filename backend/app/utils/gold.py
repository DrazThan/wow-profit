def format_gold(copper: int) -> str:
    if copper < 0:
        sign = "-"
        copper = abs(copper)
    else:
        sign = ""
    g = copper // 10000
    s = (copper % 10000) // 100
    c = copper % 100
    if g:
        return f"{sign}{g}g {s:02d}s {c:02d}c"
    if s:
        return f"{sign}{s}s {c:02d}c"
    return f"{sign}{c}c"


def after_ah_cut(buyout_copper: int) -> int:
    return int(buyout_copper * 0.95)


def flip_margin(min_buyout: int, market_value: int) -> float:
    if market_value == 0 or min_buyout == 0:
        return 0.0
    profit = after_ah_cut(market_value) - min_buyout
    return profit / market_value


def flip_profit(min_buyout: int, market_value: int) -> int:
    return after_ah_cut(market_value) - min_buyout
