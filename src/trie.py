from functools import cache
from pydantic import BaseModel


class TrieNode(BaseModel):
    children: dict[str, TrieNode] = {}
    word: str | None = None


class Trie(BaseModel):
    root: TrieNode = TrieNode()

    def add(self, word: str):
        node = self.root
        for char in word:
            node = node.children.setdefault(char, TrieNode())
        node.word = word

    def contains(self, word: str) -> bool:
        node = self.root
        for char in word:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.word == word

    @cache
    def get_words(self, prefix: str) -> list[str]:
        node = self.root
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]

        words: list[str] = []

        def fn(node: TrieNode):
            if node.word is not None:
                words.append(node.word)

            for child in node.children.values():
                fn(child)

        fn(node)

        return words
