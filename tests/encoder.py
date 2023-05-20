#!/usr/bin/env python

import binascii
import pytest       # type: ignore

from cll.encoder import Encoder


def test_rot13():
    """Test the rot13 encoding function."""
    # Create an instance of Encoder with rot13 as the encoding function
    encoder = Encoder(Encoder.rot13)
    # Test some strings with the encoder
    assert encoder("hello") == "uryyb"
    assert encoder("Bing is awesome!") == "Ovat vf njrfbzr!"
    assert encoder("Python, is fun") == "Clguba, vf sha"


def test_caesar():
    """Test the caesar encoding function."""
    encoder = Encoder(lambda s: Encoder.caesar(s, 5))

    assert encoder("hello") == "mjqqt"
    assert encoder("Bing is awesome!") == "Gnsl nx fbjxtrj!"
    assert encoder("Python, is fun") == "Udymts, nx kzs"


def test_caesar_inverse():
    """Test that the caesar encoding and decoding functions are inverses of each other."""
    encoder = Encoder(lambda s: Encoder.caesar(s, 5))
    decoder = Encoder(lambda s: Encoder.caesar(s, -5))

    assert decoder(encoder("hello")) == "hello"
    assert decoder(encoder("Bing is awesome!")) == "Bing is awesome!"
    assert decoder(encoder("Python is fun")) == "Python is fun"


def test_base64_encode():
    """Test the base64 encoding function."""
    encoder = Encoder(Encoder.base64_encode)

    assert encoder("hello") == "aGVsbG8"
    assert encoder("Bing is awesome!") == "QmluZw aXM YXdlc29tZQ!"
    assert encoder("Python, is fun!") == "UHl0aG9u, aXM ZnVu!"


def test_base64_decode():
    """Test the base64 encoding function."""
    decoder = Encoder(Encoder.base64_decode)

    assert decoder("aGVsbG8") == "hello"
    assert decoder("QmluZw aXM YXdlc29tZQ!") == "Bing is awesome!"
    assert decoder("UHl0aG9u, aXM ZnVu!") == "Python, is fun!"


def test_reverse():
    """Test the reverse encoding function."""
    encoder = Encoder(Encoder.reverse)

    assert encoder("hello") == "olleh"
    assert encoder("Bing is awesome!") == "gniB si emosewa!"
    assert encoder("Python, is fun!") == "nohtyP, si nuf!"


def test_base64_inverse():
    """Test that the base64 encoding and decoding functions are inverses of each other."""
    encoder = Encoder(Encoder.base64_encode)
    decoder = Encoder(Encoder.base64_decode)

    assert decoder(encoder("")) == ""
    assert decoder(encoder("hello")) == "hello"
    assert decoder(encoder("Bing is awesome!")) == "Bing is awesome!"
    assert decoder(encoder("Python is fun")) == "Python is fun"
    longstring = (
        "This is a long string that will be encoded and decoded. "
        "The quick brown fox jumps over the lazy dog. "
        "More lorem ipsum dolor sit amet, consectetur adipiscing elit, "
        "sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."
    )
    assert decoder(encoder(longstring)) == longstring


def test_base64_invalid():
    """Test that the base64 decoding function raises an exception with invalid input."""
    decoder = Encoder(Encoder.base64_decode)

    with pytest.raises((binascii.Error, UnicodeDecodeError)):
        decoder("hello")
    with pytest.raises((binascii.Error, UnicodeDecodeError)):
        decoder("Bing is awesome!")
    with pytest.raises((binascii.Error, UnicodeDecodeError)):
        decoder("Python is fun")


def test_map_punctuation():
    """Test that the map function does not encode punctuation."""
    encoder = Encoder(Encoder.base64_encode)

    assert encoder("hello") == "aGVsbG8"
    assert encoder("Bing is awesome!") == "QmluZw aXM YXdlc29tZQ!"
    assert encoder("Python, is fun!") == "UHl0aG9u, aXM ZnVu!"
