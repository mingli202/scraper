from files import Files


class Diff:
    def __init__(self, files: Files) -> None:
        self.files = files

    def get(self):
        pass


if __name__ == "__main__":
    files = Files()

    diff = Diff(files)
