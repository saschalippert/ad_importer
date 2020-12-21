import itertools

from numpy import mean
from sqlitedict import SqliteDict

from dota_draft_database import DotaDraftDatabase
from utils.match_utils import get_skill_heroes, get_valid_skills, get_valid_heroes, get_uniques, enrich_match, \
    set_identifiers, enrich_heroes, enrich_skills
from utils.math_utils import get_primes


def add_wl(item, win):
    if win:
        item["won"] = item.get("won", 0) + 1
    else:
        item["lost"] = item.get("lost", 0) + 1


def add_kd(item, player):
    item["kills"] = item.get("kills", 0) + player.get("kills", 0)
    item["deaths"] = item.get("deaths", 0) + player.get("deaths", 0)


def add_stats_wl(item):
    item["total"] = item.get("won", 0) + item.get("lost", 0)
    item["win_ratio"] = item.get("won", 0) / item.get("total", 0)


def add_stats_kd(item):
    kills = item.get("kills", 0)
    deaths = item.get("deaths", 0)
    total = item.get("total", 0)

    item["kd_ratio"] = kills

    if deaths > 0:
        item["kd_ratio"] = kills / deaths

    item["avg_kills"] = kills

    if total > 0:
        item["avg_kills"] = kills / total


def calc_stat(items, stat):
    values = []

    for item in items.values():
        values.append(item[stat])

    return {
        "min": min(values),
        "max": max(values),
        "avg": mean(values)
    }


def calc_stats(items, stats):
    calculated = {}

    for stat in stats:
        calculated[stat] = calc_stat(items, stat)

    calculated["count"] = len(items)

    return calculated


def main():
    sql_dict = SqliteDict('/home/sascha/Downloads/matches_db.sqlite', autocommit=True)
    database = DotaDraftDatabase()

    print(f"{len(sql_dict)} matches in db")

    database.drop()

    matches = sql_dict.values()
    matches = [m for m in matches]

    print("analysing skills and heroes")

    skill_ids, hero_ids = get_skill_heroes(matches)
    valid_skills = get_valid_skills(skill_ids)
    valid_heroes = get_valid_heroes(hero_ids)

    unique_skills = get_uniques(valid_skills)
    unique_heroes = get_uniques(valid_heroes)

    primes = get_primes(len(unique_skills) + len(unique_heroes))

    set_identifiers(unique_skills, primes)
    set_identifiers(unique_heroes, primes[len(unique_skills):])

    enrich_skills(unique_skills)
    enrich_heroes(unique_heroes)

    prime_lookup = {}

    for skill in unique_skills.values():
        prime_lookup[skill["name"]] = skill["prime"]

    print("analysing matches")

    combos = {}

    for match in matches:
        if enrich_match(match, valid_skills):
            radiant_win = match['radiant_win']

            for player in match['players']:
                is_radiant = player["player_slot"] < 5

                unique_hero = unique_heroes[player["hero_name"]]
                add_kd(unique_hero, player)
                add_wl(unique_hero, is_radiant == radiant_win)

                player_skills = player["valid_skills"]

                for skill in player_skills:
                    unique_skill = unique_skills[skill]
                    add_kd(unique_skill, player)
                    add_wl(unique_skill, is_radiant == radiant_win)

                player_combos = itertools.combinations(player_skills, 2)

                for sk1, sk2 in player_combos:
                    p1 = prime_lookup[sk1]
                    p2 = prime_lookup[sk2]

                    p_all = p1 * p2

                    combo = combos.get(p_all, {
                        "combo": [sk1, sk2],
                        "won": 0,
                        "lost": 0,
                        "kills": 0,
                        "deaths": 0
                    })

                    add_kd(combo, player)
                    add_wl(combo, is_radiant == radiant_win)

                    combos[p_all] = combo

            database.col_matches.insert_one(match)

    print("analysing skills")
    for skill in unique_skills.values():
        add_stats_wl(skill)
        add_stats_kd(skill)

    print("analysing heroes")
    for hero in unique_heroes.values():
        add_stats_wl(hero)
        add_stats_kd(hero)

    print("analysing combos")
    for prime, combo in combos.items():
        combo["prime"] = prime
        add_stats_wl(combo)
        add_stats_kd(combo)

    database.col_skills.insert_many(list(unique_skills.values()))
    database.col_heroes.insert_many(list(unique_heroes.values()))
    database.col_combos.insert_many(list(combos.values()))

    stats = ["win_ratio", "kd_ratio", "avg_kills"]

    database.col_stats_skills.insert_one(calc_stats(unique_skills, stats))
    database.col_stats_heroes.insert_one(calc_stats(unique_heroes, stats))
    database.col_stats_combos.insert_one(calc_stats(combos, stats))

    sql_dict.close()


if __name__ == '__main__':
    main()
