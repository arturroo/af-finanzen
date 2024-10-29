class TechInfo:
    def __init__(self, tech_info: dict) -> None:
        self.training_dt = tech_info['training_dt']
        self.vectorizer_fn = tech_info['vectorizer_fn']
        self.model_fn = tech_info['model_fn']
        self.test_text = tech_info['test_text']
        self.month = tech_info['month']
        self.tech_info = tech_info

    def get_all(self) -> dict:
        return self.tech_info
    
