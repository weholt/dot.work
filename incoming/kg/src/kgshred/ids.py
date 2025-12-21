"""Unique ID generation for kgshred nodes.

Implements blake2s-based content-addressed IDs with 4-char short_id collision resolution.
"""

from __future__ import annotations

import hashlib
from collections.abc import Set
from typing import NamedTuple

# Crockford Base32 alphabet (excludes I, L, O, U to avoid ambiguity)
CROCKFORD_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

# Maximum collision resolution attempts before giving up
MAX_COLLISION_ATTEMPTS = 1000


class IDGenerationError(Exception):
    """Raised when ID generation fails."""

    pass


class ShortIDResult(NamedTuple):
    """Result of short ID generation with collision resolution."""

    short_id: str
    nonce: int


def generate_full_id(
    doc_id: str,
    start: int,
    end: int,
    kind: str,
    content: bytes,
) -> str:
    """Generate a content-addressed full ID using blake2s.

    The full ID is a deterministic hash of all identifying properties
    of a node, ensuring content integrity.

    Args:
        doc_id: Document identifier.
        start: Start byte offset.
        end: End byte offset.
        kind: Node kind (heading, paragraph, etc.).
        content: Raw content bytes.

    Returns:
        32-character hexadecimal string (16 bytes).
    """
    hasher = hashlib.blake2s(digest_size=16)
    hasher.update(doc_id.encode("utf-8"))
    hasher.update(start.to_bytes(8, "little"))
    hasher.update(end.to_bytes(8, "little"))
    hasher.update(kind.encode("utf-8"))
    hasher.update(content)
    return hasher.hexdigest()


def encode_crockford_base32(data: bytes, length: int = 4) -> str:
    """Encode bytes to Crockford Base32 string.

    Crockford Base32 uses a 32-character alphabet that excludes
    ambiguous characters (I, L, O, U).

    Args:
        data: Bytes to encode.
        length: Desired output length.

    Returns:
        Uppercase Crockford Base32 string.
    """
    # Convert bytes to integer
    value = int.from_bytes(data, "big")

    # Extract 5-bit chunks from high bits
    result = []
    for _ in range(length):
        # Shift to get next 5 bits from the top
        shift = max(0, value.bit_length() - 5)
        if value == 0:
            result.append(CROCKFORD_ALPHABET[0])
        else:
            index = (value >> shift) & 0x1F
            result.append(CROCKFORD_ALPHABET[index])
            # Remove the used bits
            mask = (1 << shift) - 1
            value = value & mask

    return "".join(result)


def _compute_short_id_from_full(full_id: str, nonce: int) -> str:
    """Compute 4-char short ID from full ID with nonce.

    Args:
        full_id: Full hexadecimal ID.
        nonce: Collision resolution nonce.

    Returns:
        4-character Crockford Base32 short ID.
    """
    if nonce == 0:
        # Use first 20 bits (2.5 bytes) of full_id directly
        data = bytes.fromhex(full_id[:6])  # 3 bytes = 24 bits
    else:
        # Re-hash with nonce for collision resolution
        hasher = hashlib.blake2s(digest_size=16)
        hasher.update(full_id.encode("utf-8"))
        hasher.update(nonce.to_bytes(4, "little"))
        data = hasher.digest()[:3]

    return encode_crockford_base32(data, 4)


def generate_short_id(
    full_id: str,
    existing_ids: Set[str] | None = None,
) -> ShortIDResult:
    """Generate a unique 4-character short ID from full ID.

    Uses Crockford Base32 encoding of the first 20 bits.
    If collision occurs, increments nonce and re-hashes until unique.

    Args:
        full_id: Full hexadecimal ID to derive short ID from.
        existing_ids: Set of existing short IDs to check for collisions.

    Returns:
        ShortIDResult with short_id and nonce used.

    Raises:
        IDGenerationError: If unable to resolve collision after max attempts.
    """
    if existing_ids is None:
        existing_ids = set()

    for nonce in range(MAX_COLLISION_ATTEMPTS):
        short_id = _compute_short_id_from_full(full_id, nonce)

        if short_id not in existing_ids:
            return ShortIDResult(short_id=short_id, nonce=nonce)

    msg = f"Could not generate unique short_id after {MAX_COLLISION_ATTEMPTS} attempts"
    raise IDGenerationError(msg)


def decode_crockford_base32(encoded: str) -> int:
    """Decode Crockford Base32 string to integer.

    Handles both upper and lowercase, and normalizes ambiguous characters.

    Args:
        encoded: Crockford Base32 encoded string.

    Returns:
        Decoded integer value.

    Raises:
        ValueError: If invalid character encountered.
    """
    # Normalize: uppercase and replace ambiguous chars
    normalized = encoded.upper()
    normalized = normalized.replace("I", "1")
    normalized = normalized.replace("L", "1")
    normalized = normalized.replace("O", "0")

    value = 0
    for char in normalized:
        try:
            index = CROCKFORD_ALPHABET.index(char)
        except ValueError:
            msg = f"Invalid Crockford Base32 character: {char}"
            raise ValueError(msg) from None
        value = (value << 5) | index

    return value


def is_valid_short_id(short_id: str) -> bool:
    """Check if a string is a valid short ID.

    Valid short IDs are exactly 4 characters using Crockford Base32 alphabet.

    Args:
        short_id: String to validate.

    Returns:
        True if valid short ID format.
    """
    if len(short_id) != 4:
        return False

    normalized = short_id.upper()
    normalized = normalized.replace("I", "1")
    normalized = normalized.replace("L", "1")
    normalized = normalized.replace("O", "0")

    return all(c in CROCKFORD_ALPHABET for c in normalized)
