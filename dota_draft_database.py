import pymongo


class DotaDraftDatabase:

    def __init__(self):
        self.client = pymongo.MongoClient("mongodb://localhost:27017/")
        self.database = self.client["dota_draft"]
        self.col_skills = self.database["skills"]
        self.col_heroes = self.database["heroes"]
        self.col_matches = self.database["matches"]
        self.col_combos = self.database["combos"]

    def drop(self):
        self.client.drop_database("dota_draft")
