# metadata.py
from guidelines import GUIDELINES


class MetadataFramework:
    """
    Fournit des méthodes pour accéder aux guidelines du reporting municipal.
    """
    def __init__(self):
        self.guidelines = GUIDELINES

    def get_all_indicators(self):
        return [g["Indicateur"] for g in self.guidelines]

    def get_indicator_info(self, indicator_name):
        for g in self.guidelines:
            if g["Indicateur"].lower() == indicator_name.lower():
                return g
        return None

    def get_indicators_by_dimension(self, dimension):
        return [g for g in self.guidelines if g["Dimension"].lower() == dimension.lower()]
