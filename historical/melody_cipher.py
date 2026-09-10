#!/usr/bin/env python3
"""
Melody Cipher command-line tool.

This script encodes plain text into musical notes using various cipher methods.

Available ciphers:

- duochroma: Base-12 Chromatic scale (C, C#, D, D#, E, F, F#, G, G#, A, A#, B).
- octatonic_half_whole: Base-8 Octatonic Half-Whole (E, F, G, G#, A#, B, C#, D).
- locrian_plus2: Base-8 Locrian + 2 (E, F, F#, G, A, Bb, C, D).
- dorian_flat2: Base-8 Dorian ♭2 (E, F, G, A, B, C, C#, D).
- diminished_octatonic_whole_half: Base-8 Diminished Octatonic Whole-Half (E, F#, G, A, A#, B, C, D#).
- bebop_mixolydian: Base-8 Jazzy Bebop Mixolydian (E, F#, G#, A, B, C#, D, D#).

Usage examples:

  python melody_cipher.py --cipher duochroma --text "Hello"

  python melody_cipher.py --cipher octatonic_half_whole --file message.txt

  echo "Secret" | python melody_cipher.py --cipher bebop_mixolydian

"""

import argparse
import sys


def encode_base12(text, notes):
    """Encode text using a base-12 chromatic scale."""
    result = []
    for ch in text:
        code = ord(ch)
        high = code // 12
        low = code % 12
        # ensure indices wrap within range
        result.append(notes[high % 12])
        result.append(notes[low])
    return result


def encode_base8(text, notes):
    """Encode text using a base-8 scale. Letters A-Z map to two-note pairs; other characters handled gracefully."""
    result = []
    for ch in text:
        if ch.isalpha():
            idx = ord(ch.upper()) - ord('A')
            if 0 <= idx < 26:
                high = idx // 8
                low = idx % 8
                result.append(notes[high])
                result.append(notes[low])
            else:
                # Unknown alphabetic character
                result.append('?')
        elif ch == ' ':
            # preserve space as a marker (we treat as separate token)
            result.append(' ')
        elif ch == '\n':
            # newline preserved
            result.append('\n')
        else:
            # Unknown characters replaced with '?'
            result.append('?')
    return result


def main():
    """Main function to parse arguments and output encoded notes."""
    ciphers = {
        'duochroma': ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'],
        'octatonic_half_whole': ['E', 'F', 'G', 'G#', 'A#', 'B', 'C#', 'D'],
        'locrian_plus2': ['E', 'F', 'F#', 'G', 'A', 'Bb', 'C', 'D'],
        'dorian_flat2': ['E', 'F', 'G', 'A', 'B', 'C', 'C#', 'D'],
        'diminished_octatonic_whole_half': ['E', 'F#', 'G', 'A', 'A#', 'B', 'C', 'D#'],
        'bebop_mixolydian': ['E', 'F#', 'G#', 'A', 'B', 'C#', 'D', 'D#'],
    }
    parser = argparse.ArgumentParser(description="Encode text into musical notes using Melody Cipher.")
    parser.add_argument("--cipher", required=True, choices=list(ciphers.keys()), help="Cipher type to use.")
    parser.add_argument("--text", help="Plain text to encode. If omitted, read from --file or stdin.")
    parser.add_argument("--file", help="Path to a text file to encode.")
    args = parser.parse_args()

    # Determine input text
    input_text = None
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                input_text = f.read()
        except Exception as e:
            sys.exit(f"Error reading file: {e}")
    elif args.text is not None:
        input_text = args.text
    else:
        # Read from stdin
        input_text = sys.stdin.read()

    if input_text is None:
        sys.exit("No input text provided.")

    # Select notes for cipher
    notes = ciphers[args.cipher]

    # Encode text
    if args.cipher == 'duochroma':
        encoded_tokens = encode_base12(input_text, notes)
    else:
        encoded_tokens = encode_base8(input_text, notes)

    # Build output while preserving spaces and newlines
    line_tokens = []
    for token in encoded_tokens:
        if token == '\n':
            # Print accumulated tokens and start new line
            if line_tokens:
                print(' '.join(line_tokens))
                line_tokens = []
            print()  # newline for empty lines
        elif token == ' ':
            # Represent space by an empty string to separate words
            line_tokens.append(' ')
        else:
            line_tokens.append(token)

    # Print any remaining tokens
    if line_tokens:
        print(' '.join(line_tokens))


if __name__ == "__main__":
    main()
