# class Email:
#     human_query: str

class Email:
    def __init__(self, mensaje="", subject="", to =""):
        self._mensaje = mensaje  
        self._subject = subject
        self._to = to
    
    # Getters
    def get_mensaje(self):
        return self._mensaje
    
    def get_subject(self):
        return self._subject
    
    def get_to(self):
        return self._to
    
    # Setters
    def set_mensaje(self, mensaje):
        self._mensaje = mensaje
    
    def set_subject(self, subject):
        self._subject = subject
    
    def set_to(self, to):
        self._to = to
