import re
import unicodedata
import logging
from pathlib import Path

logger = logging.getLogger(Path(__file__).name)

LEET = str.maketrans({
    "@": "a",
    "4": "a",
    "3": "e",
    "1": "i",
    "!": "i",
    "0": "o",
    "$": "s",
    "5": "s",
    "7": "t",
})


def load_prohibited_words() -> list:
    '''
    This function fetches the prohibited words from a fixed path txt file.
    
    Returns:
        - list: list of prohibited words as strings.
    '''
    words = []
    
    current_file = Path(__file__)
    project_root = current_file.parents[2]
    file_path = project_root / "config" / "prohibition_list.txt"
    
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            words = file.read().splitlines()
    except FileNotFoundError:
        logger.error(f"Could not find file at {file_path}")
        
    return words


def normalize_for_filter(text: str) -> str:
    '''
    Normalizes text so the filter has an esier time detecting prohibitied words.
    Parameter:
        - text(str): User inputted text.
    Returns: 
        - str: normalized text for the filter to use.
    '''
    # 1. Standardize unicode symbols to plain letters
    text = unicodedata.normalize("NFKC", text).lower()
    text = text.translate(LEET)

    # 2. Remove zero-width characters trying to split words
    text = re.sub(r"[\u200b-\u200f\u2060\ufeff]", "", text)

    # 3. FIX: Strip punctuation but keep spaces (\s) so sentences don't merge
    text = re.sub(r"[^\w\s]+|_", "", text)

    # 4. Collapse excessive repeated letters (e.g., "fuuuuck" -> "fuck")
    text = re.sub(r"(.)\1{2,}", r"\1", text)

    return text


def hard_filter_text(text: str, replacement: str = "[filtered]") -> str:
    """
    Replaces exact blocked words with a filler token to protect TTS output.
    Uses the normalized text to then replace the words in the input text string
    to keep a maximum of the original text.
    
    Parameter:
        - text(str): User input text
        - replacement(str): The word that replaces the prhibootied 
    Returns:
        - string: Filtered text to send to tts server for inference.
    """
    retval = ""
    blocked_words = load_prohibited_words()
    
    if not text:
        logger.info("No text received")
        retval = ""
    elif not blocked_words:
        logger.error("No blocked words list found, returning empty message")
        retval = text
    else:
        # Create a pattern that catches bad words with extra letters attached
        pattern = r'\b\w*(?:' + '|'.join(map(re.escape, blocked_words)) + r')\w*\b'
        
        # Split the original text into words to inspect them one by one
        original_words = text.split()
        filtered_words = []

        for word in original_words:
            # Normalize just this one word to check it
            normalized_word = normalize_for_filter(word)
            
            # If the normalized word triggers the bad word pattern, replace it
            if re.search(pattern, normalized_word, flags=re.IGNORECASE):
                filtered_words.append(replacement)
            else:
                filtered_words.append(word)

        # Join the words back into a normal sentence
        retval = " ".join(filtered_words)

    return retval



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")
    try:
        while True:
            in_text = input("->")
            logger.info(hard_filter_text(in_text))
    except KeyboardInterrupt:
        logger.info("Program exited")