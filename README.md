This project was created to randomly generate encounters for D&D 5e pre-2024
It uses as a default the random encounter tables from Xanathar's guide (xanny)
but is designed to easily handle new folder to pull from. It has a few other
capabilities like rolling dice (roll()) and generating a random set of stats.
Try running this:

```
python -i toolkit.py
generator('xanny','arctic',7,'h')
```

in the terminal to test it out! It will generate the encounter, pull up the 
statblocks on Aidedd (not affiliated), and generate the loot based on the XP
of the monsters modified by monster number.

Major updates coming:
- ally mode
- damage tracking
- hoard loot
- reconfiguring encounter to be Encounter objects 
