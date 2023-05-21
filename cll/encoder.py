#!/usr/bin/env python

import base64

from dataclasses import dataclass
from typing import Callable
import re


@dataclass
class Encoder:
    """
    Encode each word of the input with a cypher.
    """

    callback: Callable[[str], str]

    def __init__(self, callback):
        """Initialize the encoder with an encoding function."""
        self.callback = callback

    def __call__(self, string):
        """Encode the string with the encoding function."""
        return self.map(string, self.callback)

    def map(self, string, callback):
        """Go through the string, extracting each word and applying the callback."""
        # Split the string by non-word characters and keep them as separate elements
        parts = re.split(r"(\W+)", string)
        # Apply the callback only to the elements that are words and leave the punctuation as it is
        return "".join([callback(part) if part.isalnum() else part for part in parts])

    @staticmethod
    def rot13(string):
        """Encode the string with rot13."""
        # Create a translation table for rot13
        table = str.maketrans(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
            "NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm",
        )
        # Translate the string using the table
        return string.translate(table)

    @staticmethod
    def base64_encode(string):
        """Encode the string with base64."""
        # Convert the string to bytes
        b = string.encode()
        b64 = base64.b64encode(b)
        return b64.decode().rstrip('=')

    @staticmethod
    def base64_decode(string):
        """Decode the string with base64."""
        # Convert the string to bytes
        b64 = string.encode() + b'=='
        b = base64.b64decode(b64)
        return b.decode().rstrip('=')

    @staticmethod
    def caesar(string, shift):
        """Encode the string with a Caesar cipher with the given shift."""
        # Create a list of uppercase letters
        uppercase = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        # Create a list of lowercase letters
        lowercase = list("abcdefghijklmnopqrstuvwxyz")
        # Create a list of shifted uppercase letters
        shifted_uppercase = uppercase[shift:] + uppercase[:shift]
        # Create a list of shifted lowercase letters
        shifted_lowercase = lowercase[shift:] + lowercase[:shift]
        # Create a translation table for the Caesar cipher
        table = str.maketrans(
            "".join(uppercase + lowercase),
            "".join(shifted_uppercase + shifted_lowercase),
        )
        # Translate the string using the table
        return string.translate(table)

    @staticmethod
    def reverse(string):
        return string[::-1]

    @staticmethod
    def none(string):
        return string

    @staticmethod
    def get_encoder(string):
        return Encoder(Encoder._get_encoder(string))

    @staticmethod
    def _get_encoder(string):
        if string in ['base64', 'b64']:
            return Encoder.base64_encode
        elif string in ['reverse', 'rev']:
            return Encoder.reverse
        elif string.startswith('rot') or string.startswith('caesar'):
            # Get the number from the string
            parts = re.split(r"(\d+)", string)
            # Get the number from the string
            number = int(parts[1])
            # Get the encoding function
            return lambda s: Encoder.caesar(s, number)

        return Encoder.none

    @staticmethod
    def get_decoder(string):
        return Encoder(Encoder._get_decoder(string))

    @staticmethod
    def _get_decoder(string):
        if string in ['base64', 'b64']:
            return Encoder.base64_decode
        elif string in ['reverse', 'rev']:
            return Encoder.reverse
        elif string.startswith('rot') or string.startswith('caesar'):
            # Get the number from the string
            parts = re.split(r"(\d+)", string)
            # Get the number from the string
            number = int(parts[1])
            # Get the encoding function
            return lambda s: Encoder.caesar(s, -number)

        return Encoder.none
