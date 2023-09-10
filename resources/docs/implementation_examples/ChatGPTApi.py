from src.ChatGptSuperClass import ChatGptSuperClass

class svs_body_handler(ChatGptSuperClass):

    def __init__(self, text_body):
        self.message = [{"role": "system",
                         "content": """Given the below text generate five technical Keywords, three technical Concepts and a 300 word technical Summary.
                                    Return the answer as a python dictionary as {Keywords: list, Concepts: list, Summary: str}"""}]
        self.message.append({"role": "user",
                             "content": self.message_inp})
        super().__init__()
        self.keywords = None
        self.concepts = None
        self.summary = None
        self._function_generator()
        self.response_parser()

    def response_parser(self):
        self.keywords = self.response['Keywords']
        self.concepts = self.response['Concepts']
        self.summary = self.response['Summary']

    def _function_generator(self):
        self.function = [
            {
                "name": "text_analyser",
                "description": "Given a text generate five technical Keywords, three technical Concepts and a 300 word technical Summary",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "Text": {
                            "type": "string",
                            "description": "The text to be processed",
                        },
                    },
                    "required": ["Text"],
                },
            }
        ]

    def get_keywords(self):
        return self.keywords

    def get_concepts(self):
        return self.concepts

    def get_summary(self):
        return self.summary