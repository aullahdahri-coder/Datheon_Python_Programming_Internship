"""Console Hangman game.

Run: python hangman.py
Optional: place a 'words.txt' (one word per line) next to this file to use
your own downloaded English word list. Otherwise a built-in list is used.
"""

import os
import random

MAX_MISTAKES = 6

DEFAULT_WORDS = [
    "python", "hangman", "keyboard", "program", "variable", "function",
    "computer", "developer", "algorithm", "internet", "network", "database",
    "terminal", "software", "library", "compiler", "elephant", "mountain",
    "adventure", "challenge", "umbrella", "notebook", "universe", "rainbow",
]

STAGES = [
    """
      +---+
      |   |
          |
          |
          |
          |
    =========
    """,
    """
      +---+
      |   |
      O   |
          |
          |
          |
    =========
    """,
    """
      +---+
      |   |
      O   |
      |   |
          |
          |
    =========
    """,
    """
      +---+
      |   |
      O   |
     /|   |
          |
          |
    =========
    """,
    """
      +---+
      |   |
      O   |
     /|\\  |
          |
          |
    =========
    """,
    """
      +---+
      |   |
      O   |
     /|\\  |
     /    |
          |
    =========
    """,
    """
      +---+
      |   |
      O   |
     /|\\  |
     / \\  |
          |
    =========
    """,
]


def load_words(filename="words.txt"):
    """Load words from file if present, else fall back to the built-in list."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            words = [w.strip().lower() for w in f
                     if w.strip().isalpha() and len(w.strip()) >= 4]
        if words:
            return words
    return DEFAULT_WORDS


def mask_word(word, guessed):
    return " ".join(c if c in guessed else "_" for c in word)


def get_guess(guessed):
    """Prompt until a valid, new single letter is entered."""
    while True:
        guess = input("Guess a letter: ").strip().lower()
        if len(guess) != 1 or not guess.isalpha():
            print("Please enter a single letter (a-z).")
        elif guess in guessed:
            print(f"You already guessed '{guess}'. Try another letter.")
        else:
            return guess


def play_round(word):
    guessed = set()
    mistakes = 0

    while mistakes < MAX_MISTAKES:
        print(STAGES[mistakes])
        print("Word:   ", mask_word(word, guessed))
        print("Guessed:", ", ".join(sorted(guessed)) or "-")
        print(f"Attempts left: {MAX_MISTAKES - mistakes}\n")

        guess = get_guess(guessed)
        guessed.add(guess)

        if guess in word:
            print(f"Good guess! '{guess}' is in the word.")
            if all(c in guessed for c in word):
                print(STAGES[mistakes])
                print("Word:   ", mask_word(word, guessed))
                print(f"\n🎉 You won! The word was '{word}'.")
                return True
        else:
            mistakes += 1
            print(f"Sorry, '{guess}' is not in the word.")

    print(STAGES[MAX_MISTAKES])
    print(f"💀 Game over! The word was '{word}'.")
    return False


def main():
    words = load_words()
    print("=== HANGMAN ===")
    while True:
        play_round(random.choice(words))
        again = input("\nPlay again? (y/n): ").strip().lower()
        if again != "y":
            print("Thanks for playing!")
            break


if __name__ == "__main__":
    main()
