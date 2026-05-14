"""
Auctionator.lua parser.

Supports two formats:
  v2 (old): AUCTIONATOR_PRICE_DATABASE realm values are Lua tables
            { ["Item Name"] = { minBuyout, timestamp }, ... }
  v8 (new): realm values are LibCBOR-encoded binary strings.
            Item keys are item-ID strings or "gr:id:suffix" / "g:id:level" gear keys.
            Each value is { l={day: lo}, h={day: hi}, a={day: qty}, m=last_price }.

Realm key format changed between versions:
  v2: "Faerlina - Horde"  (name<space>dash<space>faction)
  v8: "Nightslayer Horde" (name<space>faction, no dash)
"""

import re
import struct


# ---------------------------------------------------------------------------
# Lua string unescaping
# ---------------------------------------------------------------------------

def _lua_unescape(data: bytes) -> bytes:
    """
    Unescape a raw Lua %q-serialised byte string extracted from a SavedVariables file.
    WoW's serialiser escapes: \" -> 0x22, \\\\ -> 0x5C, \\n -> 0x0A, \\r -> 0x0D, \\ddd -> byte.
    """
    out = bytearray()
    i = 0
    while i < len(data):
        if data[i] != 0x5C:          # not a backslash — copy as-is
            out.append(data[i])
            i += 1
            continue
        nx = data[i + 1] if i + 1 < len(data) else 0
        if nx == 0x22:               # \"  → "
            out.append(0x22); i += 2
        elif nx == 0x5C:             # \\  → \
            out.append(0x5C); i += 2
        elif nx == 0x6E:             # \n  → LF
            out.append(0x0A); i += 2
        elif nx == 0x72:             # \r  → CR
            out.append(0x0D); i += 2
        elif nx == 0x74:             # \t  → TAB
            out.append(0x09); i += 2
        elif 0x30 <= nx <= 0x39:     # \ddd decimal escape
            j = i + 1
            while j < i + 4 and j < len(data) and 0x30 <= data[j] <= 0x39:
                j += 1
            out.append(int(data[i + 1:j]) & 0xFF)
            i = j
        else:
            out.append(data[i]); i += 1
    return bytes(out)


# ---------------------------------------------------------------------------
# Minimal CBOR decoder (matches LibCBOR-1.0 / Lua behaviour)
# ---------------------------------------------------------------------------

class _CBORDecoder:
    _BREAK = object()

    def __init__(self, data: bytes) -> None:
        self.data = data
        self.pos = 0

    def _readbyte(self) -> int | None:
        if self.pos >= len(self.data):
            return None
        b = self.data[self.pos]
        self.pos += 1
        return b

    def _read(self, n: int) -> bytes:
        if n <= 0:
            return b""
        s = self.data[self.pos: self.pos + n]
        self.pos += n
        return s

    def _read_length(self, mintyp: int) -> int | None:
        if mintyp < 24:
            return mintyp
        if mintyp < 28:
            raw = self._read(2 ** (mintyp - 24))
            return int.from_bytes(raw, "big")
        return None  # reserved — return None to skip, matching Lua behaviour

    def read_object(self):
        byte = self._readbyte()
        if byte is None:
            return self._BREAK
        typ, mintyp = byte >> 5, byte & 0x1F

        if typ == 0:                 # unsigned int
            n = self._read_length(mintyp)
            return n if n is not None else 0

        if typ == 1:                 # negative int
            n = self._read_length(mintyp)
            return (-1 - n) if n is not None else 0

        if typ in (2, 3):            # byte string / utf-8 string
            n = self._read_length(mintyp)
            return self._read(n or 0).decode("utf-8", errors="replace")

        if typ == 4:                 # array
            out: list = []
            if mintyp == 31:         # indefinite length
                while True:
                    v = self.read_object()
                    if v is self._BREAK:
                        break
                    out.append(v)
            else:
                n = self._read_length(mintyp) or 0
                for _ in range(n):
                    out.append(self.read_object())
            return out

        if typ == 5:                 # map
            out_map: dict = {}
            if mintyp == 31:
                while True:
                    k = self.read_object()
                    if k is self._BREAK:
                        break
                    v = self.read_object()
                    if isinstance(k, (str, int, float)):
                        out_map[k] = v
            else:
                n = self._read_length(mintyp) or 0
                for _ in range(n):
                    k = self.read_object()
                    v = self.read_object()
                    if isinstance(k, (str, int, float)):
                        out_map[k] = v
            return out_map

        if typ == 6:                 # semantic tag — skip tag, return tagged value
            self._read_length(mintyp)
            return self.read_object()

        # typ == 7: float / special / break
        if mintyp == 31:
            return self._BREAK
        if mintyp == 25:
            raw = self._read(2)
            return struct.unpack(">e", raw)[0] if len(raw) == 2 else 0.0
        if mintyp == 26:
            raw = self._read(4)
            return struct.unpack(">f", raw)[0] if len(raw) == 4 else 0.0
        if mintyp == 27:
            raw = self._read(8)
            return struct.unpack(">d", raw)[0] if len(raw) == 8 else 0.0
        return None


def _decode_cbor(blob: bytes) -> dict:
    dec = _CBORDecoder(blob)
    result = dec.read_object()
    return result if isinstance(result, dict) else {}


# ---------------------------------------------------------------------------
# Realm key normalisation
# ---------------------------------------------------------------------------

_FACTION_SUFFIXES = (" Horde", " Alliance", " Neutral")


def _split_realm_key_v8(key: str) -> tuple[str, str]:
    """
    v8 format: "RealmName Faction" (e.g. "Nightslayer Horde")
    Returns (realm_lower, faction_lower).
    """
    for suffix in _FACTION_SUFFIXES:
        if key.endswith(suffix):
            realm = key[: -len(suffix)].strip().lower()
            faction = suffix.strip().lower()
            return realm, faction
    # Fallback: treat everything as realm, faction unknown
    return key.lower(), "unknown"


def _split_realm_key_v2(key: str) -> tuple[str, str]:
    """
    v2 format: "RealmName - Faction" (e.g. "Faerlina - Horde")
    """
    parts = key.rsplit(" - ", 1)
    if len(parts) == 2:
        return parts[0].strip().lower(), parts[1].strip().lower()
    return key.lower(), "unknown"


# ---------------------------------------------------------------------------
# Item-key → item_id extraction
# ---------------------------------------------------------------------------

def _item_id_from_key(key: str) -> int | None:
    """
    Auctionator dbKey formats:
      "23572"              → plain item, id=23572
      "gr:9807:of the Boar" → gear with random suffix, base id=9807
      "g:23572:213"        → gear with item level, id=23572
      "p:1234"             → battle pet — skip
    Returns the item ID integer, or None to skip.
    """
    if key.startswith("p:"):
        return None
    if key.startswith("gr:") or key.startswith("g:"):
        parts = key.split(":")
        if len(parts) >= 2:
            try:
                return int(parts[1])
            except ValueError:
                return None
        return None
    try:
        return int(key)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

ParsedRealm = dict[int, tuple[int, int]]   # item_id → (min_buyout_copper, scan_ts)
ParsedDB = dict[str, dict[str, ParsedRealm]]  # "realm" → {"faction": ParsedRealm}


def parse_auctionator_lua(content: str | bytes) -> dict[str, dict[str, dict[int, int]]]:
    """
    Parse Auctionator.lua SavedVariables (v2 or v8 format).

    Returns:
        {
          "realm_lower": {
            "faction_lower": {
              item_id: min_buyout_copper,
              ...
            }
          }
        }
    """
    raw = content if isinstance(content, bytes) else content.encode("utf-8", errors="replace")

    # Detect version
    dbversion = 2
    m = re.search(rb'\["__dbversion"\]\s*=\s*(\d+)', raw)
    if m:
        dbversion = int(m.group(1))

    if dbversion >= 8:
        return _parse_v8(raw)
    return _parse_v2(raw.decode("utf-8", errors="replace"))


# ---------------------------------------------------------------------------
# v2 parser  (old format — Lua table of {minBuyout, timestamp} tuples)
# ---------------------------------------------------------------------------

def _parse_v2(content: str) -> dict[str, dict[str, dict[int, int]]]:
    result: dict[str, dict[str, dict[int, int]]] = {}

    realm_pattern = re.compile(
        r'\["([^"]+)"\]\s*=\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}',
        re.DOTALL,
    )
    item_pattern = re.compile(
        r'\["([^"]+)"\]\s*=\s*\{\s*(\d+)\s*,\s*(\d+)\s*\}'
    )

    for realm_match in realm_pattern.finditer(content):
        realm_key = realm_match.group(1)
        if realm_key.startswith("__") or " - " not in realm_key:
            continue
        realm, faction = _split_realm_key_v2(realm_key)
        block = realm_match.group(2)

        items: dict[int, int] = {}
        for item_match in item_pattern.finditer(block):
            price = int(item_match.group(2))
            if price <= 0:
                continue
            # v2 keys are item names — caller resolves to item_id
            # Store temporarily under name; ingest_service resolves
            try:
                name = item_match.group(1)
                items[name] = price  # type: ignore[assignment]
            except Exception:
                pass

        if items:
            result.setdefault(realm, {})[faction] = items  # type: ignore[assignment]

    return result  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# v8 parser  (new format — LibCBOR binary blob per realm)
# ---------------------------------------------------------------------------

def _parse_v8(raw: bytes) -> dict[str, dict[str, dict[int, int]]]:
    result: dict[str, dict[str, dict[int, int]]] = {}

    db_start = raw.find(b"AUCTIONATOR_PRICE_DATABASE")
    if db_start == -1:
        return result

    # Find all realm-key = "..." entries inside AUCTIONATOR_PRICE_DATABASE
    # We scan byte-by-byte after the opening brace of AUCTIONATOR_PRICE_DATABASE
    search_from = db_start

    # Pattern: ["RealmName Faction"] = "...binary..."
    key_pattern = re.compile(rb'\["([^"]+)"\]\s*=\s*"', re.DOTALL)

    pos = search_from
    while pos < len(raw):
        m = key_pattern.search(raw, pos)
        if not m:
            break

        realm_key_bytes = m.group(1)
        # Stop if we've left AUCTIONATOR_PRICE_DATABASE (next global variable)
        if realm_key_bytes == b"__dbversion":
            pos = m.end()
            continue
        # If key doesn't look like a realm key, stop scanning for realm blocks
        try:
            realm_key = realm_key_bytes.decode("utf-8")
        except Exception:
            pos = m.end()
            continue

        # Sanity: realm key should not contain = or {
        if b"=" in realm_key_bytes or b"{" in realm_key_bytes:
            pos = m.end()
            continue

        str_start = m.end()

        # Find matching closing " (skip Lua escape sequences)
        p = str_start
        while p < len(raw):
            if raw[p] == 0x22 and raw[p - 1] != 0x5C:  # unescaped "
                break
            p += 1
        escaped_blob = raw[str_start:p]
        pos = p + 1  # advance past closing "

        if not escaped_blob:
            continue

        # Check for " - " style v2 key vs v8 style
        if b" - " in realm_key_bytes:
            realm, faction = _split_realm_key_v2(realm_key)
        else:
            # Check it ends with a faction name
            has_faction = any(realm_key.endswith(s.strip()) for s in _FACTION_SUFFIXES)
            if not has_faction:
                continue
            realm, faction = _split_realm_key_v8(realm_key)

        # Decode the CBOR blob
        try:
            blob = _lua_unescape(escaped_blob)
            cbor_data = _decode_cbor(blob)
        except Exception:
            continue

        items: dict[int, int] = {}
        for db_key, entry in cbor_data.items():
            if not isinstance(entry, dict):
                continue
            item_id = _item_id_from_key(str(db_key))
            if item_id is None:
                continue
            m_val = entry.get("m")
            if not isinstance(m_val, (int, float)):
                continue
            price = int(m_val)
            if 0 < price < 2_000_000_000:
                # Keep highest price if item_id seen before (gear suffix collision)
                if item_id not in items or price > items[item_id]:
                    items[item_id] = price

        if items:
            result.setdefault(realm, {})[faction] = items

    return result


# ---------------------------------------------------------------------------
# TSM AppData.lua parser  (Kamoo format)
# ---------------------------------------------------------------------------

def parse_tsm_appdata_lua(content: str) -> dict[str, dict[int, dict]]:
    """
    Parse TSM AppData.lua (Kamoo format).

    Returns:
        { "realm_slug": { item_id: { min_buyout, market_value } } }
    """
    result: dict[str, dict[int, dict]] = {}

    block_pattern = re.compile(
        r'LoadData\s*\(\s*"AUCTIONDB_MARKET_VALUE"\s*,\s*"([^"]+)"\s*,\s*\[\[return\s*\{(.*?)\}\s*\]\]\s*\)',
        re.DOTALL,
    )
    row_pattern = re.compile(r'\{\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)')

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
