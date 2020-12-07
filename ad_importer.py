import itertools

from sqlitedict import SqliteDict

from dota_draft_database import DotaDraftDatabase
from utils.match_utils import get_skill_heroes, get_valid_skills, get_valid_heroes, get_uniques, enrich_match, \
    set_identifiers
from utils.math_utils import get_primes


def add_wl(item, win):
    if "won" not in item:
        item["won"] = 0

    if "lost" not in item:
        item["lost"] = 0

    if win:
        item["won"] += 1
    else:
        item["lost"] += 1


def main():
    sql_dict = SqliteDict('/home/sascha/Downloads/matches_db.sqlite', autocommit=True)
    database = DotaDraftDatabase()

    print(f"{len(sql_dict)} matches in db")

    database.drop()

    matches = sql_dict.values()

    print("analysing skills and heroes")

    skill_ids, hero_ids = get_skill_heroes(matches)
    valid_skills = get_valid_skills(skill_ids)
    valid_heroes = get_valid_heroes(hero_ids)

    unique_skills = get_uniques(valid_skills)
    unique_heroes = get_uniques(valid_heroes)

    primes = get_primes(len(unique_skills) + len(unique_heroes))

    set_identifiers(unique_skills, primes)
    set_identifiers(unique_heroes, primes[len(unique_skills):])

    prime_lookup = {}

    for skill in unique_skills.values():
        prime_lookup[skill["name"]] = skill["prime"]

    print("analysing matches")

    matches = sql_dict.values()

    combos = {}

    for match in matches:
        if enrich_match(match, valid_skills):
            radiant_win = match['radiant_win']

            for player in match['players']:
                is_radiant = player["player_slot"] < 5
                player_skills = player["valid_skills"]

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

                    if is_radiant == radiant_win:
                        combo["won"] = combo["won"] + 1
                    else:
                        combo["lost"] = combo["lost"] + 1

                    combo["kills"] = combo["kills"] + player["kills"]
                    combo["deaths"] = combo["deaths"] + player["deaths"]

                    combos[p_all] = combo

            for hero in match["radiant_heroes"]:
                add_wl(unique_heroes[hero], radiant_win)

            for hero in match["dire_heroes"]:
                add_wl(unique_heroes[hero], not radiant_win)

            for skill in match["radiant_skills"]:
                add_wl(unique_skills[skill], radiant_win)

            for skill in match["dire_skills"]:
                add_wl(unique_skills[skill], not radiant_win)

            database.col_matches.insert_one(match)

    print("analysing combos")

    for prime, combo in combos.items():
        combo["prime"] = prime
        combo["total"] = combo["won"] + combo["lost"]
        combo["win_ratio"] = combo["won"] / combo["total"]
        combo["kd_ratio"] = combo["kills"]

        if combo["deaths"] > 0:
            combo["kd_ratio"] = combo["kills"] / combo["deaths"]

        combo["avg_kills"] = combo["kills"] / combo["total"]

    database.col_skills.insert_many(list(unique_skills.values()))
    database.col_heroes.insert_many(list(unique_heroes.values()))
    database.col_combos.insert_many(list(combos.values()))

    sql_dict.close()


if __name__ == '__main__':
    main()
