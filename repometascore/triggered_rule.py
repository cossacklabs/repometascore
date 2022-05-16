from typing import Dict


class TriggeredRule:
    type_verbal: str
    field_name: str
    trigger: str
    value: str
    risk_value: float
    description: str

    def __init__(self, field_name, type_verbal, trigger, value, risk_value):
        self.field_name = field_name
        self.type_verbal = type_verbal
        self.trigger = trigger
        self.value = value
        self.risk_value = risk_value
        self.description = self.get_print()

    def get_print(self) -> str:
        return f"{self.type_verbal}. {self.field_name.capitalize()}. Rule: '{self.trigger}'. Value: '{self.value}'"

    def get_json(self) -> Dict:
        return self.__dict__.copy()
