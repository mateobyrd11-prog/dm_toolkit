from webbrowser import open as open_link
from random import randint as die
from random import randrange, choice
from numpy import dot
from urllib.parse import parse_qs, urldefrag, urlsplit
import re, bs4, requests
from xp_table import xp_table
from encounter_counts import CreatureCountError, creature_counts
dice = r'[0-9]+d[0-9]+'
plus = r'[0-9]+\+[0-9]+'
creature_name = r'`\w+(?:-\w+)*'
cr_raw = r'[0-9]+(?:/[0-9])?'
xp_raw = r'\([0-9]+'
num_range = r'^[0-9]{2,3}-[0-9]{2,3} '
gradient = {1:[1,2,3,4],2:[5,6,7,8,9,10],3:[11,12,13,14,15,16],4:[17,18,19,20]}
encounter_site = r'https://www.aidedd.org/dnd/monstres.php'
loot_site = r'https://dungeonmastertools.github.io/treasure.html'
# Keep encounter names readable while resolving AideDD's different URL slugs.
creature_aliases = {
    'deep-gnome': 'deep-gnome-svirfneblin',
    'will-o-wisp': 'will-o--wisp',
    'incubus': 'succubus',
    # The fragment tells our parser to read variant stats from the shared page.
    'kuo-toa-monitor': 'kuo-toa-whip#kuo-toa-monitor',
}


class StatBlockLookupError(ValueError):
    """A stat block could not supply the requested pre-2024 CR and XP."""


def creature_url(name):
    return encounter_site + '?vo=' + creature_aliases.get(name, name)


def choose_terrain():
    return choice(['arctic', 'coastal', 'desert', 
                   'forest', 'grassland', 'hill', 
                   'mountain', 'swamp', 'underdark', 
                   'underwater', 'urban'])


def roll(num,faces):
    set = []
    total = 0
    for i in range(num):
        result = die(1,faces)
        set.append(result)
        total += result
    return (total, set)


def stats():
    stat_list = []
    for i in range(6):
        stat_list.append(roll(2,6)[0]+6)

    return stat_list


def roll_dice(string):
    dice_list = re.findall(dice,string)

    value_list = [die.split('d') for die in dice_list]
    for i in range(len(value_list)):
        for j in range(2):
            value_list[i][j] = int(value_list[i][j])

    eval_dice = {dice_list[i]:roll(value_list[i][0],value_list[i][1])[0] for i in range(len(dice_list))}

    actual = string
    for die in dice_list:
        mod_string = re.sub(die,str(eval_dice[die]),actual)
        actual = mod_string

    return mod_string


def do_add(string):
    sentence = string.split()

    for i in range(len(sentence)):
        word = sentence[i]
        if re.search(plus,word):
            nums = word.split('+')
            nums = [int(num) for num in nums]
            total = nums[0]+nums[1]
            sentence[i] = str(total)

    evaluated = ''
    for word in sentence:
        evaluated += f'{word} '

    return evaluated


def do_div(string):
    fraction = string.split('/')
    fraction = [int(val) for val in fraction]
    quotient = fraction[0]/fraction[1]
    return quotient


def do_mult(string):
    sentence = string.split()
    
    for i in range(len(sentence)):
        if 'x' in sentence[i]:
            expression = sentence[i].split('x')
            expression = [int(val) for val in expression]
            product = expression[0]*expression[1]
            sentence[i] = str(product)

    evaluated = ''
    for word in sentence:
        evaluated += f'{word} '

    return evaluated


def eval_encounter(string):
    if re.search(dice,string):
        roll_result = roll_dice(string)

        if re.search(plus,roll_result):
            final_result = do_add(roll_result)
        else:
            final_result = roll_result
    else:
        final_result = string

    return final_result


def find_creature(string):
    links = []
    
    if re.search(creature_name,string):
            names = re.findall(creature_name,string)
            for i in range(len(names)):
                names[i] = names[i][1:]
            for name in names:
                links.append(creature_url(name))

    return links


def _get_challenge(url):
    """Read CR and XP from the requested pre-2024 stat block or variant."""
    name = parse_qs(urlsplit(url).query).get('vo', ['unknown creature'])[0]
    # Their standalone 2024 pages are not replacements for these 2014 variants.
    if name in {'mind-flayer-arcanist', 'quaggoth-thonot'}:
        raise StatBlockLookupError(
            f'AideDD has no pre-2024 stat block for {name}. '
            'Consult the 2014 Monster Manual; 2024 stats are not substituted.'
        )

    # Fragments are local variant identifiers and are not sent in HTTP requests.
    request_url, variant = urldefrag(url)
    try:
        response = requests.get(request_url, timeout=20)
    except requests.RequestException as error:
        raise StatBlockLookupError(f'Could not fetch stat block: {url}') from error
    if response.status_code != 200:
        raise StatBlockLookupError(f'Stat block returned HTTP {response.status_code}: {url}')

    soup = bs4.BeautifulSoup(response.text, features='html.parser')
    if variant:
        # The first CR/XP on this page belongs to the whip, not the monitor.
        if variant != 'kuo-toa-monitor' or name != 'kuo-toa-whip':
            raise StatBlockLookupError(f'Unsupported stat-block variant: {url}')
        paragraphs = [p.get_text(' ', strip=True) for p in soup.find_all('p')]
        text = next((p for p in paragraphs if re.search(
            r'kuo-toa monitor.*challenge rating', p, re.IGNORECASE
        )), '')
    else:
        text = soup.get_text(' ', strip=True)

    # \b starts at the word "Challenge"; optional noncapturing groups accept
    # "Challenge rating of" too. Capture group 1 is an integer or fraction (1/4).
    # \s+ requires whitespace, while \s* permits optional whitespace.
    match = re.search(
        r'\bChallenge(?:\s+rating)?(?:\s+of)?\s+(\d+(?:/\d+)?)'
        # Match literal parentheses around XP. Capture group 2 accepts digits,
        # commas, and whitespace (e.g. "25,000 XP"); IGNORECASE accepts either case.
        r'\s*\(\s*([\d,\s]+)\s*XP\s*\)', text, re.IGNORECASE
    )
    # AideDD can return HTTP 200 for an empty page, so validate the actual content.
    if not match:
        raise StatBlockLookupError(f'No CR/XP found in the requested stat block: {url}')
    cr_text, xp_text = match.groups()
    cr = do_div(cr_text) if '/' in cr_text else int(cr_text)
    xp = int(re.sub(r'[,\s]', '', xp_text))  # Accept grouped values such as 25,000 XP.
    return cr, xp


def get_cr(html):
    return _get_challenge(html)[0]


def get_xp(html):
    return _get_challenge(html)[1]


def count_creatures(crs,party_level):
    count = []

    for cr in crs:
        if cr >= party_level/2:
            count.append(1)
        else:
            count.append(0)
    
    return count


def xp_to_cr(xp,num_creatures):
    if num_creatures > 15:
        num_creatures = 15

    mods = {1:range(2),1.5:range(2,3),2:range(3,7),2.5:range(7,11),3:range(11,15),4:range(15,16)}
    for mod in mods:
        if num_creatures in mods[mod]:
            mod_xp = xp*mod
            break

    if mod_xp < 200:
        return 1

    for i in range(len(xp_table)-1,-1,-1):
        if mod_xp >= xp_table[i]:
            return i+1


def in_range(num,string):
    rnge = re.search(num_range,string).group(0)
    check_in = rnge.split('-')
    check_in = [int(val) for val in check_in]
    return num in range(check_in[0],check_in[1]+1)


def strip_range(string):
    clean = re.sub(num_range,'',string)
    return clean


def loot(cr):
    if cr < 1:
        cr = 1
    
    start = 0
    if cr > 20:
        cr = 20
        start = 50
        stop = 100

    for key in gradient:
        if round(cr) in gradient[key]:
            table = key
            break

    filename = f'loot/table_{table}.txt'
    number = roll(1,100)[0]
    
    if start:
        number = randrange(start,stop)
        
    with open(filename, 'r') as file:
        for line in file:
            if in_range(number, line):
                result = line
                break

    cleaned = strip_range(result)
    treasure = do_mult(do_add(roll_dice(cleaned)))
    clean_string = treasure.strip()
    
    return clean_string


def generator(source,terrain,level,diff=''):
    if level > 20:
        level = 20
        diff = 'h'

    
    # Preserve party level for the XP multiplier; rank only selects the source file.
    rank = level
    for key in gradient:
        if level in gradient[key]:
            rank = key
            break

    filename = f'encounters/{source}/{terrain}/rank_{rank}.txt'
    number = roll(1,100)[0]

    diff_ranges = {'e':(1,50),'m':(25,75),'h':(50,100)}
    if diff:
        start = diff_ranges[diff][0]
        stop = diff_ranges[diff][1]
        number = randrange(start,stop)

    with open(filename,'r') as encounter_file:
        for line in encounter_file:
            if in_range(number,line):
                result = line
                break

    encounter = eval_encounter(strip_range(result)).strip()
    creatures = find_creature(encounter)
    
    xps = []
    crs = []

    if creatures:
        # Resolve quantities before network/browser calls; narrative numbers are not counts.
        totals = creature_counts(encounter)
        for creature in creatures:
            xps.append(get_xp(creature))
            crs.append(get_cr(creature))
            open_link(creature)

        # Sum count * XP per creature type, then count only significant monsters
        # when selecting the group multiplier used for conversion to a loot CR.
        xp = dot(xps,totals)
        count_vector = count_creatures(crs,level)
        significant_creatures = dot(totals,count_vector)
        encounter_cr = xp_to_cr(xp,significant_creatures)
    
    if xps:
        return encounter, loot(encounter_cr)
    else:
        return encounter
