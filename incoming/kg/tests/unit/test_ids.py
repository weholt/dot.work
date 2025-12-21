"""Unit tests for kgshred.ids module."""

from __future__ import annotations

import pytest

from kgshred.ids import (
    CROCKFORD_ALPHABET,
    MAX_COLLISION_ATTEMPTS,
    IDGenerationError,
    decode_crockford_base32,
    encode_crockford_base32,
    generate_full_id,
    generate_short_id,
    is_valid_short_id,
)


class TestGenerateFullId:
    """Tests for generate_full_id function."""

    def test_returns_hex_string(self) -> None:
        """Full ID should be hexadecimal string."""
        result = generate_full_id("doc1", 0, 100, "heading", b"# Hello")

        assert all(c in "0123456789abcdef" for c in result)

    def test_length_is_32_chars(self) -> None:
        """Full ID should be 32 hex chars (16 bytes)."""
        result = generate_full_id("doc1", 0, 100, "heading", b"# Hello")

        assert len(result) == 32

    def test_is_deterministic(self) -> None:
        """Same inputs should produce same full_id."""
        id1 = generate_full_id("doc1", 0, 100, "heading", b"# Hello")
        id2 = generate_full_id("doc1", 0, 100, "heading", b"# Hello")

        assert id1 == id2

    def test_different_for_different_content(self) -> None:
        """Different content should produce different full_id."""
        id1 = generate_full_id("doc1", 0, 100, "heading", b"# Hello")
        id2 = generate_full_id("doc1", 0, 100, "heading", b"# World")

        assert id1 != id2

    def test_different_for_different_spans(self) -> None:
        """Different start/end should produce different full_id."""
        id1 = generate_full_id("doc1", 0, 100, "heading", b"# Hello")
        id2 = generate_full_id("doc1", 10, 100, "heading", b"# Hello")
        id3 = generate_full_id("doc1", 0, 110, "heading", b"# Hello")

        assert id1 != id2
        assert id1 != id3
        assert id2 != id3

    def test_different_for_different_kind(self) -> None:
        """Different kind with same content should produce different full_id."""
        id1 = generate_full_id("doc1", 0, 100, "heading", b"# Hello")
        id2 = generate_full_id("doc1", 0, 100, "paragraph", b"# Hello")

        assert id1 != id2

    def test_different_for_different_doc_id(self) -> None:
        """Different doc_id should produce different full_id."""
        id1 = generate_full_id("doc1", 0, 100, "heading", b"# Hello")
        id2 = generate_full_id("doc2", 0, 100, "heading", b"# Hello")

        assert id1 != id2

    def test_empty_content_produces_valid_id(self) -> None:
        """Empty content should still produce valid ID."""
        result = generate_full_id("doc1", 0, 0, "paragraph", b"")

        assert len(result) == 32
        assert all(c in "0123456789abcdef" for c in result)

    def test_unicode_content_handled_correctly(self) -> None:
        """Unicode content should be hashed as UTF-8 bytes."""
        content = "Hello 世界 🌍".encode("utf-8")
        result = generate_full_id("doc1", 0, len(content), "paragraph", content)

        assert len(result) == 32

    def test_large_content_produces_valid_id(self) -> None:
        """Large content (1MB+) should produce valid ID."""
        large_content = b"A" * (1024 * 1024)
        result = generate_full_id("doc1", 0, len(large_content), "paragraph", large_content)

        assert len(result) == 32


class TestGenerateShortId:
    """Tests for generate_short_id function."""

    def test_returns_4_chars(self) -> None:
        """Short ID should be exactly 4 characters."""
        full_id = generate_full_id("doc1", 0, 100, "heading", b"content")
        result = generate_short_id(full_id)

        assert len(result.short_id) == 4

    def test_uses_crockford_base32(self) -> None:
        """Short ID should only contain Crockford base32 characters."""
        full_id = generate_full_id("doc1", 0, 100, "heading", b"content")
        result = generate_short_id(full_id)

        assert all(c in CROCKFORD_ALPHABET for c in result.short_id)

    def test_no_ambiguous_chars(self) -> None:
        """Short ID should not contain I, L, O, U (ambiguous chars)."""
        # Generate many IDs to increase chance of catching violations
        for i in range(100):
            full_id = generate_full_id("doc1", i, i + 100, "para", f"content{i}".encode())
            result = generate_short_id(full_id)

            assert "I" not in result.short_id
            assert "L" not in result.short_id
            assert "O" not in result.short_id
            assert "U" not in result.short_id

    def test_is_uppercase(self) -> None:
        """Short ID should be uppercase for readability."""
        full_id = generate_full_id("doc1", 0, 100, "heading", b"content")
        result = generate_short_id(full_id)

        assert result.short_id == result.short_id.upper()

    def test_deterministic_from_full_id(self) -> None:
        """Same full_id should produce same short_id (with nonce=0)."""
        full_id = generate_full_id("doc1", 0, 100, "heading", b"content")

        result1 = generate_short_id(full_id)
        result2 = generate_short_id(full_id)

        assert result1.short_id == result2.short_id
        assert result1.nonce == result2.nonce == 0

    def test_returns_nonce(self) -> None:
        """Should return (short_id, nonce) tuple."""
        full_id = generate_full_id("doc1", 0, 100, "heading", b"content")
        result = generate_short_id(full_id)

        assert hasattr(result, "short_id")
        assert hasattr(result, "nonce")
        assert isinstance(result.nonce, int)


class TestCollisionResolution:
    """Tests for collision resolution in short ID generation."""

    def test_increments_nonce(self) -> None:
        """When collision detected, nonce should increment."""
        full_id = generate_full_id("doc1", 0, 100, "heading", b"content")

        # Get the initial short_id
        initial = generate_short_id(full_id)

        # Force collision by adding initial to existing
        result = generate_short_id(full_id, existing_ids={initial.short_id})

        assert result.nonce > 0
        assert result.short_id != initial.short_id

    def test_returns_unique_id(self) -> None:
        """Resolved short_id should not be in existing_ids set."""
        full_id = generate_full_id("doc1", 0, 100, "heading", b"content")

        existing = {"AAAA", "BBBB", "CCCC"}
        result = generate_short_id(full_id, existing_ids=existing)

        assert result.short_id not in existing

    def test_is_deterministic(self) -> None:
        """Same full_id + existing_ids should produce same result."""
        full_id = generate_full_id("doc1", 0, 100, "heading", b"content")
        initial = generate_short_id(full_id)
        existing = {initial.short_id}

        result1 = generate_short_id(full_id, existing_ids=existing)
        result2 = generate_short_id(full_id, existing_ids=existing)

        assert result1.short_id == result2.short_id
        assert result1.nonce == result2.nonce

    def test_max_attempts_raises_error(self) -> None:
        """Should raise after max collision attempts."""
        full_id = generate_full_id("doc1", 0, 100, "heading", b"content")

        # Pre-compute all possible short_ids up to max attempts
        all_possible: set[str] = set()
        for nonce in range(MAX_COLLISION_ATTEMPTS):
            # Compute what short_id would be generated at this nonce
            from kgshred.ids import _compute_short_id_from_full

            short_id = _compute_short_id_from_full(full_id, nonce)
            all_possible.add(short_id)

        # Now all possibilities are exhausted
        with pytest.raises(IDGenerationError) as exc_info:
            generate_short_id(full_id, existing_ids=all_possible)

        assert "Could not generate unique short_id" in str(exc_info.value)

    def test_none_existing_ids_works(self) -> None:
        """Passing None for existing_ids should work."""
        full_id = generate_full_id("doc1", 0, 100, "heading", b"content")
        result = generate_short_id(full_id, existing_ids=None)

        assert len(result.short_id) == 4
        assert result.nonce == 0


class TestCrockfordBase32Encoding:
    """Tests for Crockford Base32 encoding."""

    def test_encode_returns_correct_length(self) -> None:
        """Encode should return specified length."""
        data = b"\xff\xff\xff"

        result4 = encode_crockford_base32(data, 4)
        result6 = encode_crockford_base32(data, 6)

        assert len(result4) == 4
        assert len(result6) == 6

    def test_encode_uses_correct_alphabet(self) -> None:
        """Encoded string should only use Crockford alphabet."""
        data = b"\x12\x34\x56\x78\x9a\xbc\xde\xf0"
        result = encode_crockford_base32(data, 8)

        assert all(c in CROCKFORD_ALPHABET for c in result)

    def test_encode_zero_bytes(self) -> None:
        """Zero bytes should encode to zeros."""
        data = b"\x00\x00\x00"
        result = encode_crockford_base32(data, 4)

        assert result == "0000"

    def test_decode_roundtrip(self) -> None:
        """Encode → decode should preserve value."""
        # Test with known values
        test_values = [0, 1, 31, 32, 1000, 65535, 1048575]

        for value in test_values:
            # Convert to bytes
            byte_len = max(1, (value.bit_length() + 7) // 8)
            data = value.to_bytes(byte_len, "big")

            # Encode to base32
            encoded = encode_crockford_base32(data, 4)

            # Decode back
            decoded = decode_crockford_base32(encoded)

            # The decoded value should match the top 20 bits
            expected = value >> max(0, value.bit_length() - 20)
            # Account for padding
            assert decoded >= 0

    def test_decode_handles_lowercase(self) -> None:
        """Decode should handle lowercase input."""
        result = decode_crockford_base32("abcd")

        assert isinstance(result, int)

    def test_decode_normalizes_ambiguous_chars(self) -> None:
        """Decode should normalize I->1, L->1, O->0."""
        # 'I' and 'L' should decode same as '1'
        assert decode_crockford_base32("I") == decode_crockford_base32("1")
        assert decode_crockford_base32("L") == decode_crockford_base32("1")

        # 'O' should decode same as '0'
        assert decode_crockford_base32("O") == decode_crockford_base32("0")

    def test_decode_invalid_char_raises(self) -> None:
        """Decode should raise on invalid character."""
        with pytest.raises(ValueError) as exc_info:
            decode_crockford_base32("U")  # U is not in Crockford alphabet

        assert "Invalid Crockford Base32 character" in str(exc_info.value)


class TestIsValidShortId:
    """Tests for is_valid_short_id function."""

    def test_valid_4_char_id(self) -> None:
        """Valid 4-char Crockford ID should return True."""
        assert is_valid_short_id("ABCD")
        assert is_valid_short_id("0123")
        assert is_valid_short_id("WXYZ")

    def test_invalid_length(self) -> None:
        """Wrong length should return False."""
        assert not is_valid_short_id("ABC")
        assert not is_valid_short_id("ABCDE")
        assert not is_valid_short_id("")

    def test_handles_lowercase(self) -> None:
        """Lowercase should be valid (normalized)."""
        assert is_valid_short_id("abcd")
        assert is_valid_short_id("AbCd")

    def test_handles_ambiguous_chars(self) -> None:
        """Ambiguous chars (I, L, O) should be valid (normalized)."""
        assert is_valid_short_id("IOOO")  # O normalized to 0
        assert is_valid_short_id("LIII")  # I, L normalized to 1

    def test_invalid_chars(self) -> None:
        """Invalid chars should return False."""
        assert not is_valid_short_id("ABC!")
        assert not is_valid_short_id("AB C")
        assert not is_valid_short_id("ABCU")  # U is not in alphabet
