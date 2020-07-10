# Tested with Python 3.6.9

import argparse
import requests
from functools import reduce
from tabulate import tabulate

# === HTTP request wrappers === #
def GET_PAGINATED(req: callable):
  acc = []
  page = 1
  while True:
    res = req(page)
    acc.extend(res['data'])
    page += 1
    if len(res['data']) <= 0:
      return acc

def GET(url: str): # basic WG API GET request handling
  print(f"GET {url}")
  res = requests.get(url)
  if res.status_code != 200 or res.json()['status'] != 'ok':
    raise Exception(f"HTTP Status: {res.status_code}; Response: {res.json()}")
  return res.json()

def GET_ALL(url: str):
  return GET_PAGINATED(lambda page: GET(url + f"&page_no={page}"))

def GET_GAME_API(url: str): # basic `game_api` GET request handling (not part of WG API)
  print(f"GET {url}")
  res = requests.get(url)
  if res.status_code != 200:
    raise Exception(f"HTTP Status: {res.status_code}")
  return res.json()

def GET_ALL_GAME_API(url: str):
  return GET_PAGINATED(lambda page: GET_GAME_API(url + f"&page_number={page}"))

# === API wrappers === #
def getNumBattles(clanId: str):
  res = GET_GAME_API(f"https://eu.wargaming.net/globalmap/game_api/clan/{clanId}/log?category=battles&page_size=1")
  return res['meta']['total_count']

def getBattleLogs(clanId: str):
  numBattles = getNumBattles(clanId)
  res = GET_ALL_GAME_API(f"https://eu.wargaming.net/globalmap/game_api/clan/{clanId}/log?category=battles&page_size={numBattles}")
  if len(res) != numBattles:
    raise Exception(f"Received incomplete")
  return res

def getAllFrontIds():
  res = GET_ALL(f"https://api.worldoftanks.eu/wot/globalmap/fronts/?application_id={APPLICATION_ID}&fields=front_id")
  return set(map(lambda x: x['front_id'], res))

def getFrontsOfProvinces(frontIds: set):
  output = {}
  for frontId in frontIds:
    res = GET_ALL(f"https://api.worldoftanks.eu/wot/globalmap/provinces/?application_id={APPLICATION_ID}&front_id={frontId}&fields=province_id")
    for province in res:
      output[province['province_id']] = frontId
  return output

# === parse and format data === #
def isVictory(battle: list):
  return battle['type'].endswith("_WON")

def isDefeat(battle: list):
  return battle['type'].endswith("_LOST")

def isDraw(battle: list):
  return battle['type'].endswith("_DRAW")

def getClanData(battles: list, frontOfProvince: dict, frontIds: set):
  clanData = {}

  for battle in battles:
    # skip "battles" which weren't real battles (i.e. leaving map) and all battles on other fronts
    provinceId = battle['target_province'].get('alias')
    frontId = frontOfProvince.get(provinceId)
    if not (isVictory(battle) or isDefeat(battle) or isDraw(battle)) or frontId == None:
      continue

    clanId = battle['enemy_clan']['id']
    # init clanData[clanId] for all fronts
    if clanData.get(clanId) == None:
      clanData[clanId] = { 'name': battle['enemy_clan']['tag'] }
      for frontId in frontIds:
        clanData[clanId][frontId] = { 'victory': 0, 'defeat': 0, 'draw': 0 }

    if isVictory(battle):
      clanData[clanId][frontId]['victory'] += 1
    elif isDefeat(battle):
      clanData[clanId][frontId]['defeat'] += 1
    elif isDraw(battle):
      clanData[clanId][frontId]['draw'] += 1

  return clanData

def formatRow(clan: dict, frontIds: set):
  numBattles = reduce(lambda acc, curr: acc + clan[curr]['victory'] + clan[curr]['defeat'] + clan[curr]['draw'], frontIds, 0)
  numVictories = reduce(lambda acc, curr: acc + clan[curr]['victory'], frontIds, 0)
  winRate = "-" if numBattles == 0 else '{:.3f}'.format(numVictories / numBattles)
  return [clan['name'], numBattles, winRate]

def printClanData(clanData: dict, frontIds: set):
  output = map(lambda clanId: formatRow(clanData[clanId], frontIds), clanData.keys())
  output = filter(lambda x: x[1] > 0, output)
  output = sorted(output, key = lambda x: x[1], reverse = True)
  table = tabulate(output, headers=['Clan', 'Battles', 'Winrate'])

  print(f"Displaying data for fronts: {frontIds}")
  print(table)

# === main === #
parser = argparse.ArgumentParser(prog='wot-campaign-winrate.py', description='Get winrates split up by front of World of Tanks campaign.')
parser.add_argument('applicationId', type=str, help='Application ID in for the WG API')
parser.add_argument('clanId', type=str, help='ID of the clan')
parser.add_argument('frontIds', type=str, nargs='*', help='IDs of the fronts for which to display stats; can be left empty to use all')
args = parser.parse_args()

APPLICATION_ID = args.applicationId

frontIds = set(args.frontIds) if len(args.frontIds) > 0 else getAllFrontIds()
frontsOfProvinces = getFrontsOfProvinces(frontIds)
battles = getBattleLogs(args.clanId)
clanData = getClanData(battles, frontsOfProvinces, frontIds)
printClanData(clanData, frontIds)
