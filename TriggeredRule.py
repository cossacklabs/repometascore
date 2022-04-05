class TriggeredRule:
    type: str = str()
    fieldName: str = str()
    trigger: str = str()
    value: str = str()
    riskValue: float = float()

    def getPrint(self):
        return f"{self.type}. {self.fieldName.capitalize()}. Rule: '{self.trigger}'. Value: '{self.value}'"
