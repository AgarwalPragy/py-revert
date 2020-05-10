from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

import revert
from revert.orm import Entity
from revert.orm.attributes import BackReference, BackReferences, CalculatedField, CalculatedMultiRelation, Field, MultiRelation, Relation, UnionRelation
from revert.orm.constraints import Constraint, Contributes, FormulaDependency, FullTextSearch, Index, OnChange, OneToOne, Reverse, SortedIndex, Unique


class NoteStats(Entity):
    ctr = CalculatedField(float)
    note = BackReference(lambda: BaseNote)

    views = Field(int)
    clicks = Field(int)
    votes = Field(int)

    def _formula_ctr(self) -> float:
        return self.clicks / (self.views + 1.0)

    @classmethod
    def attribute_constraints(cls) -> List[Constraint]:
        return super().attribute_constraints() + [
            SortedIndex(cls.ctr),
            FormulaDependency(cls.ctr, dependency=cls.clicks),
            FormulaDependency(cls.ctr, dependency=cls.views),
        ]


class BaseNote(Entity, ABC):
    children = UnionRelation(lambda: BaseNote)
    parents = UnionRelation(lambda: BaseNote)
    extracted = BackReferences(lambda: BaseNote)
    shelves = BackReferences(lambda: Shelf)
    stats = BackReference(lambda: NoteStats)
    title = CalculatedField(str)
    searchable_text = CalculatedField(str)

    access_level = Field(str)
    source = Relation(lambda: BaseNote)

    def __init__(self, access_level: str = 'default'):
        pass
        # Shelf.get(name='orphans').notes.add(self)

    def check_orphan(self):
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

    @abstractmethod
    def _formula_searchable_text(self, trigger: str) -> str:
        ...

    @abstractmethod
    def _formula_title(self, trigger: str) -> str:
        ...

    @classmethod
    def attribute_constraints(cls) -> List[Constraint]:
        return super().attribute_constraints() + [
            OneToOne(NoteStats.note, cls.stats),
            Index(cls.access_level),
            FullTextSearch(cls.searchable_text),
            FullTextSearch(cls.title),
            Reverse(cls.extracted, cls.source),
            Reverse(cls.parents, cls.children),
            OnChange(cls.parents, trigger=cls.check_orphan),
            Contributes(cls.source, to=cls.parents),
            Contributes(cls.extracted, to=cls.children),
        ]


class MarkdownNote(BaseNote):
    references = CalculatedMultiRelation(lambda: BaseNote)
    referenced_by = BackReferences(lambda: MarkdownNote)
    tagged_by = BackReferences(lambda: MarkdownNote)

    content = Field(str)
    tags = MultiRelation(lambda: BaseNote)

    def _formula_references(self) -> List[BaseNote]:
        print(self)
        return []

    def _formula_searchable_text(self, trigger: str) -> str:
        return self.content

    def _formula_title(self, trigger: str) -> str:
        return [stripped for line in self.content.split('\n') if (stripped := line.strip())][0]

    @classmethod
    def attribute_constraints(cls) -> List[Constraint]:
        return super().attribute_constraints() + [
            FormulaDependency(cls.searchable_text, dependency=cls.content),
            FormulaDependency(cls.title, dependency=cls.content),
            FormulaDependency(cls.references, dependency=cls.content),
            Reverse(cls.references, cls.referenced_by),
            Reverse(cls.tags, cls.tagged_by),
            Contributes(cls.references, to=cls.children),
            Contributes(cls.referenced_by, to=cls.parents),
            Contributes(cls.tags, to=cls.parents),
            Contributes(cls.tagged_by, to=cls.children),
        ]


class VocabNote(BaseNote):
    word = Field(str)
    meaning = Field(str)
    synonyms = MultiRelation(lambda: BaseNote)
    antonyms = MultiRelation(lambda: BaseNote)

    def _formula_searchable_text(self, trigger: str) -> str:
        return self.word + self.meaning

    def _formula_title(self, trigger: str) -> str:
        return f'{self.word} (Vocab)'

    @classmethod
    def attribute_constraints(cls) -> List[Constraint]:
        return super().attribute_constraints() + [
            FormulaDependency(cls.searchable_text, dependency=cls.word),
            FormulaDependency(cls.searchable_text, dependency=cls.meaning),
            FormulaDependency(cls.title, dependency=cls.word),
            Reverse(cls.synonyms, cls.synonyms),
            Reverse(cls.antonyms, cls.antonyms),
            Contributes(cls.synonyms, to=cls.parents),
            Contributes(cls.synonyms, to=cls.children),
            Contributes(cls.antonyms, to=cls.parents),
            Contributes(cls.antonyms, to=cls.children),
        ]


class ResourceNote(BaseNote, ABC):
    mime = Field(str)
    url = Field(str)
    metadata = Field(str)

    @abstractmethod
    def _formula_searchable_text(self, trigger: str) -> str:
        ...

    @abstractmethod
    def _formula_title(self, trigger: str) -> str:
        ...

    @classmethod
    def attribute_constraints(cls) -> List[Constraint]:
        return super().attribute_constraints() + [
            FormulaDependency(cls.searchable_text, dependency=cls.url),
            FormulaDependency(cls.searchable_text, dependency=cls.metadata),
            FormulaDependency(cls.title, dependency=cls.metadata),
            Index(cls.mime),
            Index(cls.url),
            Unique(cls.url),
        ]


class DefaultResourceNote(ResourceNote):
    def _formula_searchable_text(self, trigger: str) -> str:
        return self.url + self.metadata

    def _formula_title(self, trigger: str) -> str:
        return self.metadata

    @classmethod
    def attribute_constraints(cls) -> List[Constraint]:
        return super().attribute_constraints() + [
            FormulaDependency(cls.title, dependency=cls.metadata),
        ]


class VideoRN(ResourceNote, ABC):
    pass


class YoutubeVRN(VideoRN):
    captions = Field(str)
    description = Field(str)
    video_title = Field(str)

    def _formula_searchable_text(self, trigger: str) -> str:
        return self.url + self.metadata + self.captions + self.description + self.video_title

    def _formula_title(self, trigger: str) -> str:
        return self.video_title

    @classmethod
    def attribute_constraints(cls) -> List[Constraint]:
        return super().attribute_constraints() + [
            FormulaDependency(cls.searchable_text, dependency=cls.captions),
            FormulaDependency(cls.searchable_text, dependency=cls.description),
            FormulaDependency(cls.searchable_text, dependency=cls.video_title),
            FormulaDependency(cls.title, dependency=cls.video_title),
        ]


class WikipediaRN(ResourceNote):
    pass


class StackOverflowRN(ResourceNote):
    question_title = Field(str)
    question = Field(str)
    selected_answer = Field(str)
    other_top_answer = Field(str)

    def _formula_searchable_text(self, trigger: str) -> str:
        return self.question_title + self.question + self.selected_answer + self.other_top_answer + self.metadata + self.url

    def _formula_title(self, trigger: str) -> str:
        return self.question_title

    @classmethod
    def attribute_constraints(cls) -> List[Constraint]:
        return super().attribute_constraints() + [
            FormulaDependency(cls.searchable_text, dependency=cls.question_title),
            FormulaDependency(cls.searchable_text, dependency=cls.question),
            FormulaDependency(cls.searchable_text, dependency=cls.selected_answer),
            FormulaDependency(cls.searchable_text, dependency=cls.other_top_answer),
            FormulaDependency(cls.title, dependency=cls.question_title),
        ]


class ImageRN(ResourceNote):
    pass


class FileRN(ResourceNote):
    pass


class Shelf(Entity):
    votes = Field(int)
    name = Field(str)
    notes = MultiRelation(lambda: BaseNote)

    def __init__(self, name: str) -> None:
        self.name = name

    @classmethod
    def attribute_constraints(cls) -> List[Constraint]:
        return super().attribute_constraints() + [
            Reverse(Shelf.notes, BaseNote.shelves),
            Unique(Shelf.name),
            Index(Shelf.name),
        ]


if __name__ == '__main__':
    revert.connect('db/')
    with revert.Transaction():
        orphans = Shelf('orphans')
        python = MarkdownNote()
        python.content = 'Python Programming Language'
        programming = MarkdownNote()
        programming.content = 'Programming'
        python.tags.add(programming)
    print(list(python.tags)[0].content)
    revert.undo()
    print('after undo')
    print(list(python.tags)[0].content)
