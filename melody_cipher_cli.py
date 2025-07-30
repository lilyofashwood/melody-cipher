#!/usr/bin/env python3
"""
Melody Cipher command-line tool.

This script encodes or decodes text into musical notes using various cipher methods.

Available ciphers:

- duochroma: Base-12 Chromatic scale (C, C#, D, D#, E, F, F#, G, G#, A, A#, B).
- octatonic_half_whole: Base-8 Octatonic Half-Whole (E, F, G, G#, A#, B, C#, D).
- locrian_plus2: Base-8 Locrian + 2 (E, F, F#, G, A, Bb, C, D).
- dorian_flat2: Base-8 Dorian ♭2 (E, F, G, A, B, C, C#, D).
- diminished_octatonic_whole_half: Base-8 Diminished Octatonic Whole-Half (E, F#, G, A, A#, B, C, D#).
- bebop_mixolydian: Base-8 Jazzy Bebop Mixolydian (E, F#, G#, A, B, C#, D, D#).

Usage examples:

  # Encode plain text
  python melody_cipher_cli.py --cipher duochroma --text "Hello"

  # Decode a sequence of notes (space encoded as '/')
  python melody_cipher_cli.py --cipher octatonic_half_whole --decode --text "E F G E / C# D A# F"

  # Read from a file and decode
  python melody_cipher_cli.py --cipher bebop_mixolydian --decode --file encoded.txt

Notes:
- When encoding with base 8 ciphers, spaces in the original message are represented by the token '/'.
- When decoding, provide note names separated by spaces. Use '/' to indicate a space character in the original text.
- Newlines should be represented as actual newline characters in the encoded input; they will be preserved on decode.
"""

import argparse
import sys


def encode_base12(text, notes):
    """Encode text using a base 12 chromatic scale."""
    result = []
    for ch in text:
        code = ord(ch)
        high = code // 12
        low = code % 12
        result.append(notes[high % 12])
        result.append(notes[low])
    return result


def encode_base8(text, notes):
    """Encode text using a base 8 scale. Letters A–Z map to two‑note pairs; spaces map to '/'."""
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
                result.append('?')
        elif ch == ' ':
            result.append('/')  # represent a space
        elif ch == '\n':
            result.append('\\n')  # newline marker
        else:
            result.append('?')
    return result


def decode_base12(tokens, notes):
    """Decode a sequence of note tokens into text using a base 12 scale."""
    result = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok == '/':
            result.append(' ')
            i += 1
        elif tok == '\\n':
            result.append('\n')
            i += 1
        elif tok == '?':
            result.append('?')
            i += 1
        else:
            if i + 1 >= len(tokens):
                result.append('?')
                break
            tok2 = tokens[i + 1]
            if tok2 in ['/', '\\n', '?']:
                result.append('?')
                i += 1
                continue
            try:
                high = notes.index(tok)
                low = notes.index(tok2)
                code = (high * 12) + low
                result.append(chr(code))
            except ValueError:
                result.append('?')
            i += 2
    return ''.join(result)


def decode_base8(tokens, notes):
    """Decode a sequence of note tokens into letters using a base 8 scale."""
    result = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok == '/':
            result.append(' ')
            i += 1
        elif tok == '\\n':
            result.append('\n')
            i += 1
        elif tok == '?':
            result.append('?')
            i += 1
        else:
            if i + 1 >= len(tokens):
                result.append('?')
                break
            tok2 = tokens[i + 1]
            if tok2 in ['/', '\\n', '?']:
                result.append('?')
                i += 1
                continue
            try:
                high = notes.index(tok)
                low = notes.index(tok2)
                idx = (high * 8) + low
                if 0 <= idx < 26:
                    result.append(chr(ord('A') + idx))
                else:
                    result.append('?')
            except ValueError:
                result.append('?')
            i += 2
    return ''.join(result)


def main():
    ciphers = {
        'duochroma': ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'],
        'octatonic_half_whole': ['E','F','G','G#','A#','B','C#','D'],
        'locrian_plus2': ['E','F','F#','G','A','Bb','C','D'],
        'dorian_flat2': ['E','F','G','A','B','C','C#','D'],
        'diminished_octatonic_whole_half': ['E','F#','G','A','A#','B','C','D#'],
        'bebop_mixolydian': ['E','F#','G#','A','B','C#','D','D#'],
    }

    parser = argparse.ArgumentParser(description="Encode or decode text to musical notes using Melody Cipher.")
    parser.add_argument("--cipher", required=True, choices=list(ciphers.keys()), help="Cipher type to use.")
    parser.add_argument("--text", help="Input text (plain text for encoding or note sequence for decoding).")
    parser.add_argument("--file", help="Path to a file containing input text.")
    parser.add_argument("--decode", action="store_true", help="Decode a sequence of notes instead of encoding.")
    args = parser.parse_args()

    # Determine input data
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                input_data = f.read()
        except Exception as e:
            sys.exit(f"Error reading file: {e}")
    elif args.text is not None:
        input_data = args.text
    else:
        input_data = sys.stdin.read()

    notes = ciphers[args.cipher]

    if args.decode:
        # Split input into lines and tokens
        lines = input_data.splitlines()
        decoded_lines = []
        for line in lines:
            if not line.strip():
                decoded_lines.append('')
                continue
            tokens = line.strip().split()
            if args.cipher == 'duochroma':
                decoded_lines.append(decode_base12(tokens, notes))
            else:
                decoded_lines.append(decode_base8(tokens, notes))
        print('\n'.join(decoded_lines))
    else:
        # Encode input text
        if args.cipher == 'duochroma':
            tokens = encode_base12(input_data, notes)
        else:
            tokens = encode_base8(input_data, notes)
        # Build string preserving newline markers
        output_lines = []
        current_tokens = []
        for token in tokens:
            if token == '\\n':
                output_lines.append(' '.join(current_tokens))
                current_tokens = []
                output_lines.append('')  # represent blank line
            else:
                current_tokens.append(token)
        if current_tokens:
            output_lines.append(' '.join(current_tokens))
        print('\n'.join(output_lines))

if __name__ == "__main__":
    main()
