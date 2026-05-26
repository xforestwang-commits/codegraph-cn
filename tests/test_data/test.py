
def hello():
    '''Say hello.'''
    print("Hello, World!")

class User:
    def __init__(self, name):
        self.name = name

    def greet(self):
        return f"Hello, {self.name}!"

def main():
    user = User("CodeGraph")
    user.greet()
