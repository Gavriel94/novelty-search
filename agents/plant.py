class Plant():
    def __init__(self, sustenance_granted: float):
        self.sustenance_granted = sustenance_granted
    
    def sustenance(self) -> float:
        return self.sustenance_granted
        