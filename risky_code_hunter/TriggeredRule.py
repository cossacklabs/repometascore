from typing import Dict


class TriggeredRule:
    type: str
    fieldName: str
    trigger: str
    value: str
    riskValue: float
    description: str

    def __init__(self, fieldName, type, trigger, value, riskValue):
        self.fieldName = fieldName
        self.type = type
        self.trigger = trigger
        self.value = value
        self.riskValue = riskValue
        self.description = self.getPrint()

    def getPrint(self) -> str:
        return f"{self.type}. {self.fieldName.capitalize()}. Rule: '{self.trigger}'. Value: '{self.value}'"

    def getJSON(self) -> Dict:
        return self.__dict__.copy()
