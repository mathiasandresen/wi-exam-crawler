class Corpus:
    
    corpus = []

    def __init__(self, output):
        self.output = output

    def add(self, value: tuple[str, str]):

        if (value[0] is None or value[1] is None):
            return
    
        self.corpus.append(value)
        f = open(self.output, "a", encoding="UTF-8")

        title = repr(value[0]).strip('\'')
        title = title.replace(";", "<<semicolon>>")
        url =  value[1]

        f.writelines(["{};{}".format(title, url), '\n'])
        f.close()

    def has_url(self, url) -> bool:
        for element in self.corpus:
            if element[1] == url:
                return True
        return False