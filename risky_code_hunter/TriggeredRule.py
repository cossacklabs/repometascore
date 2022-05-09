from typing import Dict


class TriggeredRule:
    type: str
    fieldName: str
    trigger: str
    value: str
    riskValue: float
    description: str

    def __init__(self, field_name, type_verbal, trigger, value, risk_value):
        self.fieldName = field_name
        self.type = type_verbal
        self.trigger = trigger
        self.value = value
        self.riskValue = risk_value
        self.description = self.get_print()

    def get_print(self) -> str:
        return f"{self.type}. {self.fieldName.capitalize()}. Rule: '{self.trigger}'. Value: '{self.value}'"

    def get_json(self) -> Dict:
        return self.__dict__.copy()
