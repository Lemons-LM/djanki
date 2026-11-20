"""Minimal namespace registry for the first model version.

The registry is deliberately a Python mapping rather than a database table. A later
migration can promote it to a ``Namespace`` model without changing title keys.
"""

MAIN = 0
TALK = 1
USER = 2
USER_TALK = 3
PROJECT = 4
PROJECT_TALK = 5
FILE = 6
FILE_TALK = 7
MEDIAWIKI = 8
MEDIAWIKI_TALK = 9
TEMPLATE = 10
TEMPLATE_TALK = 11
HELP = 12
HELP_TALK = 13
CATEGORY = 14
CATEGORY_TALK = 15

NAMESPACE_NAMES = {
    MAIN: "",
    TALK: "Talk",
    USER: "User",
    USER_TALK: "User talk",
    PROJECT: "Project",
    PROJECT_TALK: "Project talk",
    FILE: "File",
    FILE_TALK: "File talk",
    MEDIAWIKI: "MediaWiki",
    MEDIAWIKI_TALK: "MediaWiki talk",
    TEMPLATE: "Template",
    TEMPLATE_TALK: "Template talk",
    HELP: "Help",
    HELP_TALK: "Help talk",
    CATEGORY: "Category",
    CATEGORY_TALK: "Category talk",
}

# Namespaces whose first letter is case-insensitive for lookup purposes.
FIRST_LETTER_CASE_NAMESPACES = {MAIN, PROJECT, TEMPLATE, HELP, CATEGORY}


def namespace_name(namespace: int) -> str:
    """Return the display name for a namespace, or an empty string for main."""
    return NAMESPACE_NAMES.get(namespace, "")
