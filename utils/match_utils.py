import json

skill_ids = json.load(open("data/ability_ids.json"))
skill_names = {v: k for (k, v) in skill_ids.items()}
heroes = json.load(open("data/heroes.json"))

map_skills = {
    "tiny_toss_tree": skill_names["tiny_tree_grab"],
    "dark_willow_bedlam": skill_names["dark_willow_terrorize"],
    "wisp_spirits_in": skill_names["wisp_spirits"],
    'life_stealer_consume': skill_names['life_stealer_infest'],
    'keeper_of_the_light_spirit_form_illuminate': skill_names['keeper_of_the_light_illuminate'],
    'phoenix_launch_fire_spirit': skill_names['phoenix_fire_spirits'],
    'alchemist_unstable_concoction_throw': skill_names['alchemist_unstable_concoction'],
    'kunkka_return': skill_names['kunkka_x_marks_the_spot'],
    'monkey_king_primal_spring': skill_names['monkey_king_tree_dance'],
    "bane_nightmare_end": skill_names['bane_nightmare'],
}


def __filter_skills(skill, skill_filters):
    for filter in skill_filters:
        if not filter(skill):
            return False

    return True


def get_skill_name(skill_id):
    str_skill = str(skill_id)
    if str_skill in skill_ids:
        skill_name = skill_ids[str_skill]

        if skill_name in map_skills:
            skill_name = skill_ids[map_skills[skill_name]]

        return skill_name

    return None


def get_hero_name(hero_id):
    str_hero = str(hero_id)
    return heroes[str_hero]["name"].replace("npc_dota_hero_", "")


def get_skill_heroes(matches):
    skill_ids = set()
    hero_ids = set()

    for match in matches:
        for player in match["players"]:
            hero_ids.add(player["hero_id"])

            if "ability_upgrades" in player:
                for skill in player["ability_upgrades"]:
                    skill_ids.add(skill["ability"])

    return skill_ids, hero_ids


def get_valid_skills(all_skill):
    valid_skill_ids = {}
    invalid_skill_ids = []

    skill_filters = []
    skill_filters.append(lambda a: not a.startswith("special_"))
    skill_filters.append(lambda a: not a.startswith("ad_special_"))

    for skill_id in all_skill:
        str_skill_id = str(skill_id)
        skill_name = get_skill_name(skill_id)

        if skill_name:
            if __filter_skills(skill_name, skill_filters):
                valid_skill_ids[str_skill_id] = skill_name
            else:
                invalid_skill_ids.append(str_skill_id)
        else:
            invalid_skill_ids.append(str_skill_id)

    return valid_skill_ids


def get_valid_heroes(all_heroes):
    valid_hero_ids = {}

    for hero_id in all_heroes:
        str_hero = str(hero_id)
        valid_hero_ids[str_hero] = get_hero_name(str_hero)

    return valid_hero_ids


def enrich_match(match, valid_skill_ids):
    match["valid"] = True
    match_id = match["match_id"]

    match_valid_skills = {}
    dire_skills = {}
    radiant_skills = {}
    dire_heroes = []
    radiant_heroes = []

    for player in match["players"]:
        player_slot = player["player_slot"]
        hero_id = str(player["hero_id"])
        hero_name = None

        if hero_id in heroes:
            hero = heroes[hero_id]
            hero_name = hero["name"].replace('npc_dota_hero_', "")
            player["hero_name"] = hero_name
        else:
            match["valid"] = False

        player_valid_skills = {}
        player_invalid_skills = {}

        if "ability_upgrades" in player:
            player_skill_upgrades = player["ability_upgrades"]

            skilled_counter = {}

            for skill_upgrade in player_skill_upgrades:

                skill_id = str(skill_upgrade["ability"])

                if skill_id in valid_skill_ids:
                    skill_name = get_skill_name(skill_id)

                    if skill_name:
                        skilled = skilled_counter.get(skill_name, 0)
                        skilled += 1
                        skilled_counter[skill_name] = skilled

                        player_valid_skills[skill_name] = skill_id
                    else:
                        player_invalid_skills[skill_name] = skill_id

            for skill_name in player_valid_skills.keys():
                if skill_name in match_valid_skills:
                    match["valid"] = False
                    print(f"match {match_id} hero {hero_name} double draft detected {skill_name}")
        else:
            match["valid"] = False

        match_valid_skills.update(player_valid_skills)

        if player_slot < 5:
            radiant_skills.update(player_valid_skills)
            radiant_heroes.append(hero_name)
        else:
            dire_skills.update(player_valid_skills)
            dire_heroes.append(hero_name)

        player["valid_skills"] = list(player_valid_skills.keys())
        player["invalid_skills"] = list(player_invalid_skills.keys())

        len_player_valid_skills = len(player_valid_skills)
        if len_player_valid_skills < 4:
            match["valid"] = False
        elif len_player_valid_skills > 4:
            match["valid"] = False
            too_many_skills = player_valid_skills.keys()
            print(f"match {match_id} hero {hero_name} drafted too many skills {too_many_skills}")

    match["radiant_heroes"] = radiant_heroes
    match["dire_heroes"] = dire_heroes

    len_radiant_heroes = len(match["radiant_heroes"])
    len_dire_heroes = len(match["dire_heroes"])

    if len_radiant_heroes != 5 or len_dire_heroes != 5:
        match["valid"] = False
        print(f"match {match_id} hero team distribution off {len_radiant_heroes} vs {len_dire_heroes}")

    match["valid_skills"] = list(match_valid_skills.keys())
    match["radiant_skills"] = list(radiant_skills.keys())
    match["dire_skills"] = list(dire_skills.keys())

    len_valid_skills = len(match_valid_skills)
    len_radiant_skills = len(radiant_skills)
    len_dire_skills = len(dire_skills)

    if len_valid_skills < 40:
        match["valid"] = False
    elif len_valid_skills > 40:
        match["valid"] = False
        print(f"match {match_id} too many skills: {len_valid_skills}")
    elif len_radiant_skills != 20 or len_dire_skills != 20:
        match["valid"] = False
        print(f"match {match_id} skill team distribution off {len_radiant_skills} vs {len_dire_skills}")

    return match["valid"]


def get_uniques(valid_dict):
    uniques = {}

    for id, name in valid_dict.items():
        unique = uniques.get(name, {
            "ids": set(),
            "name": name,
        })

        unique["ids"].add(id)

        uniques[name] = unique

    return uniques


def set_identifiers(uniques, primes):
    for i, unique in enumerate(uniques.values()):
        unique["ids"] = list(unique["ids"])
        unique["prime"] = primes[i]
        unique["index"] = i
