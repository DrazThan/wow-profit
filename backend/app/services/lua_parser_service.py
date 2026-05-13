import re


def parse_auctionator_lua(content: str) -> dict[str, dict[str, tuple[int, int]]]:
    """
    Parse Auctionator.lua SavedVariables file.

    Returns:
        { "RealmName - Faction": { "Item Name": (minBuyout_copper, scan_timestamp) } }
    """
    result: dict[str, dict[str, tuple[int, int]]] = {}

    # Match top-level realm blocks: ["Faerlina - Horde"] = { ... }
    # The inner block may contain nested braces (item entries use { val, val })
    realm_pattern = re.compile(
        r'\["([^"]+)"\]\s*=\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}',
        re.DOTALL,
    )
    # Match individual item price entries: ["Item Name"] = { minBuyout, timestamp }
    item_pattern = re.compile(
        r'\["([^"]+)"\]\s*=\s*\{\s*(\d+)\s*,\s*(\d+)\s*\}'
    )

    for realm_match in realm_pattern.finditer(content):
        realm_key = realm_match.group(1)
        if realm_key.startswith("__"):
            continue
        # Only include realm-faction keys (they contain " - ")
        if " - " not in realm_key:
            continue
        block = realm_match.group(2)
        items: dict[str, tuple[int, int]] = {}
        for item_match in item_pattern.finditer(block):
            name = item_match.group(1)
            price = int(item_match.group(2))
            ts = int(item_match.group(3))
            if price > 0:
                items[name] = (price, ts)
        if items:
            result[realm_key] = items

    return result


def parse_tsm_appdata_lua(content: str) -> dict[str, dict[int, dict]]:
    """
    Parse TSM AppData.lua (Kamoo format).

    Returns:
        { "realm_slug": { item_id: { min_buyout, market_value } } }
    """
    result: dict[str, dict[int, dict]] = {}

    # Match: LoadData("AUCTIONDB_MARKET_VALUE","<realm>",[[return { ... }]])
    block_pattern = re.compile(
        r'LoadData\s*\(\s*"AUCTIONDB_MARKET_VALUE"\s*,\s*"([^"]+)"\s*,\s*\[\[return\s*\{(.*?)\}\s*\]\]\s*\)',
        re.DOTALL,
    )
    # Match row entries: { itemId, minBuyout, marketValue, ... }
    row_pattern = re.compile(
        r'\{\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)'
    )

    for block_match in block_pattern.finditer(content):
        realm = block_match.group(1)
        block = block_match.group(2)
        items: dict[int, dict] = {}
        for row_match in row_pattern.finditer(block):
            item_id = int(row_match.group(1))
            min_buyout = int(row_match.group(2))
            market_value = int(row_match.group(3))
            if min_buyout > 0 or market_value > 0:
                items[item_id] = {"min_buyout": min_buyout, "market_value": market_value}
        if items:
            result[realm] = items

    return result
