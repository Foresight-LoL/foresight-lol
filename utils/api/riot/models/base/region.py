from enum import StrEnum


# The AMERICAS routing value serves NA (NA1), BR (BR1), LAN (LA1) and LAS (LA2).
# The ASIA routing value serves KR (KR) and JP (JP1).
# The EUROPE routing value serves EUNE (EUN1), EUW (EUW1), ME1 (ME1), TR (TR1) and RU (RU).
# The SEA routing value serves OCE (OC1), SG2 (SG2), TW2 (TW2) and VN2 (VN2).

# There are three routing values for account-v1; americas, asia, and europe.
# You can query for any account in any region. We recommend using the nearest cluster.

class Region(StrEnum):
    @classmethod
    def _missing_(cls, value):
        value = value.__str__().strip().upper()
        for member in cls:
            if member.value == value:
                return member

        return None

    def get_higher_level_region(self):
        if self in {self.AMERICAS, self.NA, self.BR, self.LAN, self.LAS}:
            return self.AMERICAS

        if self in {self.ASIA, self.KR, self.JP}:
            return self.ASIA

        if self in {self.EUROPE, self.EUNE, self.EUW, self.ME, self.TR, self.RU}:
            return self.EUROPE

        return None

    def get_base_url(self):
        return f"https://{self.value.lower()}.api.riotgames.com"

    def get_higher_level_base_url(self):
        return f"https://{self.get_higher_level_region().value.lower()}.api.riotgames.com"

    # AMERICAS
    AMERICAS = "AMERICAS"

    NA = "NA1"
    BR = "BR1"
    LAN = "LA1"
    LAS = "LA2"

    # ASIA
    ASIA = "ASIA"

    KR = "KR1"
    JP = "JP1"

    # EUROPE
    EUROPE = "EUROPE"

    EUNE = "EUN1"
    EUW = "EUW1"
    ME = "ME1"
    TR = "TR1"
    RU = "RU1"

    # SEA
    OCE = "OCE1"
    SG = "SG2"
    TW = "TW2"
    VN = "VN2"
