from __future__ import annotations

from abc import ABC
from typing import List

import revert
from revert.orm import AutoAdd, Calculate, Constraint, Entity, Field, MultiRelation, OnChange, ProtectedField, ProtectedMultiRelation, ProtectedRelation, Relation, ReverseOf


class NoteStats(Entity):
    clicks = Field(int)
    ctr = ProtectedField(float, index=True)
    note = ProtectedRelation(lambda: BaseNote)
    views = Field(int)
    votes = Field(int)

    @classmethod
    def enforced_constraints(cls) -> List[Constraint]:
        return [
            Calculate(cls.ctr, based_on=[cls.clicks, cls.views], formula=cls._calculate_ctr)
        ]

    def _calculate_ctr(self) -> float:
        return self.clicks / (self.views + 1.0)


class BaseNote(Entity, ABC):
    access_level = Field(str, index=True)
    children = ProtectedMultiRelation(lambda: BaseNote)
    extracted = ProtectedMultiRelation(lambda: BaseNote)
    parents = ProtectedMultiRelation(lambda: BaseNote)
    searchable_text = ProtectedField(str, full_text_search=True)
    shelves = ProtectedMultiRelation(lambda: Shelf)
    source = Relation(lambda: BaseNote)
    stats = ProtectedRelation(lambda: NoteStats)
    title = ProtectedField(str, full_text_search=True)

    @classmethod
    def enforced_constraints(cls) -> List[Constraint]:
        return [
            ReverseOf(cls.extracted, cls.source),
            ReverseOf(cls.extracted, cls.source),
            ReverseOf(cls.shelves, Shelf.notes),  # enforce the other way
            ReverseOf(cls.parents, cls.children),
            OnChange(cls.parents, trigger=cls._parents_changed),
            AutoAdd(cls.source, to=cls.parents),
            AutoAdd(cls.extracted, to=cls.children),
        ]

    def __init__(self):
        pass
        # Shelf.get(name='orphans').notes.add(self)

    def _parents_changed(self):
        if not self.parents:
            Shelf.get(name='orphans').notes.add(self)
        else:
            Shelf.get(name='orphans').notes.discard(self)

    def delete(self, force=False):
        # todo: check if note is open
        if not force:
            raise Exception('Editor is open')
        Shelf.get(name='orphans').notes.discard(self)
        super().delete()


class MarkdownNote(BaseNote):
    content = Field(str)
    references = ProtectedMultiRelation(lambda: BaseNote)
    referenced_by = ProtectedMultiRelation(lambda: MarkdownNote)
    tags = MultiRelation(lambda: BaseNote)
    tagged_by = ProtectedMultiRelation(lambda: MarkdownNote)

    @classmethod
    def enforced_constraints(cls):
        return super().enforced_constraints() + [
            Calculate(cls.searchable_text, based_on=cls.content, formula=lambda self: self.content),
            Calculate(cls.title, based_on=cls.content, formula=lambda self: [stripped for line in self.content.split('\n') if (stripped := line.strip())][0]),
            Calculate(cls.references, based_on=cls.content, formula=cls._extract_references),
            ReverseOf(cls.references, cls.referenced_by),
            ReverseOf(cls.tags, cls.tagged_by),
            AutoAdd(cls.references, to=cls.children),
            AutoAdd(cls.tags, to=cls.parents),
        ]

    def _extract_references(self):
        self.references = []


class VocabNote(BaseNote):
    word = Field(str)
    meaning = Field(str)
    synonyms = MultiRelation(lambda: BaseNote)
    antonyms = MultiRelation(lambda: BaseNote)

    @classmethod
    def enforced_constraints(cls):
        return super().enforced_constraints() + [
            Calculate(cls.searchable_text, based_on=[cls.word, cls.meaning], formula=lambda self: self.word + self.meaning),
            Calculate(cls.title, based_on=cls.word, formula=lambda self: f'{self.word} (Vocab)'),
            ReverseOf(cls.synonyms, cls.synonyms),
            ReverseOf(cls.antonyms, cls.antonyms),
            AutoAdd(cls.synonyms, to=cls.parents),
            AutoAdd(cls.synonyms, to=cls.children),
            AutoAdd(cls.antonyms, to=cls.parents),
            AutoAdd(cls.antonyms, to=cls.children),
        ]


class ResourceNote(BaseNote):
    mime = Field(str)
    url = Field(str, index=True, unique=True)
    metadata = Field(str)

    @classmethod
    def enforced_constraints(cls):
        return super().enforced_constraints() + [
            Calculate(cls.searchable_text, based_on=[cls.url, cls.metadata], formula=lambda self: self.url + self.metadata),
            Calculate(cls.title, based_on=cls.metadata, formula=lambda self: self.metadata),
        ]


class VideoRN(ResourceNote):
    pass


class YoutubeVRN(VideoRN):
    captions = Field(str)
    description = Field(str)

    @classmethod
    def enforced_constraints(cls):
        return super().enforced_constraints() + [
            Calculate(cls.searchable_text, based_on=[cls.url, cls.metadata, cls.captions, cls.description],
                      formula=lambda self: self.url + self.metadata + self.captions + self.description),
        ]


class WikipediaRN(ResourceNote):
    pass


class StackOverflowRN(ResourceNote):
    question = Field(str)
    selected_answer = Field(str)
    other_top_answer = Field(str)

    @classmethod
    def enforced_constraints(cls):
        return super().enforced_constraints() + [
            Calculate(cls.searchable_text, based_on=[cls.url, cls.metadata, cls.question, cls.selected_answer, cls.other_top_answer],
                      formula=lambda self: self.url + self.metadata + self.question + self.answer + self.other_top_answer),
        ]


class ImageRN(ResourceNote):
    pass


class FileRN(ResourceNote):
    pass


class Shelf(Entity):
    votes = Field(int)
    name = Field(str, unique=True, index=True)
    notes = MultiRelation(lambda: BaseNote)

    @classmethod
    def enforced_constraints(cls):
        return [
            ReverseOf(cls.notes, BaseNote.shelves),
        ]

    def before_change(self):
        super().before_change()
        if self.name == 'orphans':
            self.votes = 0


if __name__ == '__main__':
    revert.connect('db/')
    with revert.Transaction():
        python = MarkdownNote()
        python.content = 'Python Programming Language'
        programming = MarkdownNote()
        programming.content = 'Programming'
        python.tags.add(programming)
    print(list(python.tags)[0].content)
