from appdirs import unicode


def get_valid_filename(s):
    """
    Return the given string converted to a string that can be used for a clean
    filename. Remove leading and trailing spaces; remove anything that is not an
    alphanumeric, dash, whitespace, comma, bracket, underscore, or dot.
    >>> get_valid_filename("john's portrait in 2004.jpg")
    'johns_portrait_in_2004.jpg'
    """
    s = text_to_id(s)
    s = remove_spaces(s)
    return re.sub(r'(?u)[^-\w\s.,[\]()]', '', s)


def remove_spaces(s):
    s = str(s).strip()
    s = str(s).replace(' ', '').replace(',', '_')
    return s


import re

import unicodedata


def strip_accents(text):
    """
    Strip accents from input String.

    :param text: The input string.
    :type text: String.

    :returns: The processed String.
    :rtype: String.
    """
    try:
        text = unicode(text, 'utf-8')
    except (TypeError, NameError):  # unicode is a default on python 3
        pass
    text = unicodedata.normalize('NFD', text)
    text = text.encode('ascii', 'ignore')
    text = text.decode("utf-8")
    return str(text)


def text_to_id(text):
    """
    Convert input text to id.

    :param text: The input string.
    :type text: String.

    :returns: The processed String.
    :rtype: String.
    """
    text = strip_accents(text.lower())
    text = re.sub('[ ]+', '_', text)
    text = re.sub('[^0-9a-zA-Z_-]', '', text)
    return text
