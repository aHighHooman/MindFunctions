class Body:
    def __init__(self):
        self.needs = {
            "Hunger" : 0,
            "Toilet" : 0,
            "Hygiene": 0,
        }

        self.stamina = {
            "Physical" : 0,
            "Mental"   : 0,
            "Sleep"    : 0,
        }
        return 