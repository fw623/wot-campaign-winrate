# World of Tanks campaign winrate tool
This python tool lets you analyze winrates against different clans on the Global Map during campaigns. It's also possible to look at the different fronts individually or combined.

## Usage
```bash
$ python3.6 wot-campaign-winrate.py ${APPLICATION_ID} ${CLAN_ID} ${FRONT_IDs}

# examples
$ python3.6 wot-campaign-winrate.py 123as1df321e6fe3f32 12345678 front1 front2
$ python3.6 wot-campaign-winrate.py 123as1df321e6fe3f32 12345678

# help
python3.6 wot-campaign-winrate.py -h
```

## Output
```
Displaying data for fronts: {'front1', 'front2'}
Clan      Battles    Winrate
------  ---------  ---------
CLAN1          21      0.714
CLAN2          17      0.647
CLAN3           9      0.667
CLAN4           3      0
CLAN5           1      1
```
