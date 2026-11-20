"""Associate evaluated creature markers with quantities, not narrative numbers."""
import re


class CreatureCountError(ValueError):
    """An encounter needs a choice or an explicit creature quantity."""


_WORDS = dict(zip(
    'zero one two three four five six seven eight nine ten eleven twelve '
    'thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty'.split(),
    range(21),
))
_QUANTITY = r'(?:\d+|' + '|'.join(_WORDS) + r')'
_LABEL = r'(?:[a-z][a-z\'-]*\s+){0,4}'
_COUNT = re.compile(r'(?<![\w.\-])(' + _QUANTITY + r')\s+(' + _LABEL + r')\(?\s*$', re.I)
_ARTICLE = re.compile(r'\b(?:a|an)\s+(' + _LABEL + r')\(?\s*$', re.I)
_UNITS = re.compile(
    r'\b(?:feet|foot|miles?|days?|weeks?|hours?|minutes?|seconds?|years?|'
    r'gp|sp|cp|pp|ep|percent|chance|level|xp)\b', re.I
)
_GROUP = re.compile(r'\b(?:herd|flock|group|tribe|swarm|school|force|number)\b', re.I)


def creature_counts(encounter):
    """Return quantities in marker order; reject unresolved alternatives/conditions.

    Input is encounter text after dice evaluation. Numeric or spelled-out counts
    may precede short labels, including parenthesized stat-block names. Articles
    imply one individual; mounts inherit rider counts. Unquantified groups do
    not default to one.
    """
    encounter = re.sub(r'^\d{2,3}-\d{2,3}\s+', '', encounter)
    markers = list(re.finditer(r'`([a-z]+(?:-[a-z]+)*)', encounter))
    if not markers:
        return []
    if re.search(r'\b(?:day|night)\s+only\b|\((?:day|night)\)', encounter, re.I):
        raise CreatureCountError('Resolve the day/night condition before calculating XP.')

    counts = []
    names = []
    previous_end = 0
    for marker in markers:
        prefix = encounter[previous_end:marker.start()]
        name = marker.group(1)
        if counts and re.search(r'\bor\b', prefix, re.I):
            raise CreatureCountError('Choose one alternative before calculating XP.')
        if re.search(r'\bchance\b', prefix, re.I):
            raise CreatureCountError('Resolve the chance condition before calculating XP.')

        replacement = re.search(r'\((?:one|1)\s+([a-z-]+)\s+is\s+an?\s*$', prefix, re.I)
        if replacement:
            original = replacement.group(1).lower()
            if original not in names or counts[names.index(original)] < 1:
                raise CreatureCountError(f'Cannot identify the creature replaced by {name}.')
            counts[names.index(original)] -= 1
            count = 1
        else:
            explicit = _COUNT.search(prefix)
            article = _ARTICLE.search(prefix)
            if explicit and not _UNITS.search(explicit.group(2)):
                quantity = explicit.group(1).lower()
                count = int(quantity) if quantity.isdigit() else _WORDS[quantity]
            elif counts and re.search(r'\ball\s+(?:on|riding|astride)\s*$', prefix, re.I):
                count = sum(counts)
            elif counts and re.search(r'\b(?:on|riding|astride)\s*$', prefix, re.I):
                count = counts[-1]
            elif article and not _UNITS.search(article.group(1)) and not _GROUP.search(article.group(1)):
                count = 1
            else:
                raise CreatureCountError(f'No unambiguous count for {name}; supply an explicit quantity.')

        counts.append(count)
        names.append(name)
        previous_end = marker.end()
    return counts
