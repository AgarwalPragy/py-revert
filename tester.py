from __future__ import annotations

from abc import ABC
from typing import Set, Type, TypeVar

import revert
from revert import Transaction
from revert.ogm import ClassDictField, Dict, DirectedEdge, Field, Node, ProtectedSet, SetField, UndirectedEdge

T = TypeVar('T')


class TF_IDF:
    pass


class Relation:
    pass


class DirectedRelation(DirectedEdge, Relation):
    pass


class UndirectedRelation(UndirectedEdge, Relation):
    pass


class NoteStats(Node):
    _ctr: float = Field()  # add sorted index using classvar
    _note: Note = Field()

    _views: int = Field()
    _clicks: int = Field()
    votes: int = Field()

    def __init__(self, note: Note) -> None:
        self._note = note

    @property
    def note(self) -> Note:
        return self._note

    @property
    def views(self) -> int:
        return self._views

    @views.setter
    def views(self, value: int) -> None:
        self._views = value
        self._recalculate_ctr()

    @property
    def clicks(self) -> int:
        return self._clicks

    @clicks.setter
    def clicks(self, value: int) -> None:
        self._clicks = value
        self._recalculate_ctr()

    def _recalculate_ctr(self) -> None:
        self._ctr = self.clicks / (self.views + 1.0)


class Note(Node):
    _stats: NoteStats = Field()
    access_level: str = Field()
    shelves: Set[Shelf] = SetField()

    _search_index: TF_IDF = Field()
    _title: str = Field()

    def __new__(cls, *args, **kwargs):
        if cls == Note:
            raise TypeError('Cannot create objects of abstract Note class')
        return super().__new__(cls, *args, **kwargs)

    def __init__(self):
        Shelf.shelves['orphans'].add_note(self)
        self._stats = NoteStats(self)

    def delete(self):
        self._stats.delete()
        for shelf in self.shelves:
            shelf.notes.discard(self)
        super().delete()

    def _parent_relations(self, cls: Type[Relation]) -> ProtectedSet[Note]:
        return super()._parent_relations(Source)  # type: ignore

    def _child_relations(self, cls: Type[Relation]) -> ProtectedSet[Note]:
        return super()._child_relations(Source)  # type: ignore

    @property
    def stats(self) -> NoteStats:
        return self._stats

    @property
    def sources(self) -> ProtectedSet[Note]:
        return self._parent_relations(Source)

    @property
    def extracted(self) -> ProtectedSet[Note]:
        return self._child_relations(Source)

    @property
    def title(self) -> str:
        return self._title

    @property
    def search_index(self) -> TF_IDF:
        return self._search_index

    def add_to_shelf(self, shelf: Shelf) -> None:
        self.shelves.add(shelf)
        shelf.notes.add(self)


class Shelf(Node):
    shelves: Dict[str, Shelf] = ClassDictField()
    votes: int = Field()
    _name: str = Field()
    notes: Set[Note] = SetField()

    def __init__(self, name: str) -> None:
        self._name = ''
        self.name = name

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        if value == self._name:
            return
        if not value:
            raise Exception('Invalid name')
        if value in Shelf.shelves:
            raise Exception('Duplicate name')
        if self._name:
            del Shelf.shelves[self._name]
        Shelf.shelves[value] = self
        self._name = value

    def add_note(self, note: Note) -> None:
        self.notes.add(note)
        note.shelves.add(self)

    def delete(self):
        for note in self.notes:
            note.shelves.discard(self)


class Source(DirectedRelation):
    def __init__(self, note: Note, source: Note) -> None:
        super().__init__(parent=source, child=note)


class Reference(DirectedRelation):
    def __init__(self, note: Note, reference: Note) -> None:
        super().__init__(parent=note, child=reference)


class Tag(DirectedRelation):
    def __init__(self, note: Note, tag: Note) -> None:
        super().__init__(parent=tag, child=note)


class MarkdownNote(Note):
    _content: str = Field()

    @property
    def references(self):
        return self._child_relations(Reference)

    @property
    def referenced_by(self):
        return self._parent_relations(Reference)

    @property
    def tags(self):
        return self._parent_relations(Tag)

    @property
    def tagged_by(self):
        return self._child_relations(Tag)

    @property
    def content(self) -> str:
        return self._content

    @content.setter
    def content(self, value: str) -> None:
        self._content = value
        self._title = [stripped for line in value.split('\n') if (stripped := line.strip())][0]
        # todo: extract references & searchable text


class Synonym(UndirectedRelation):
    ...


class Antonym(UndirectedRelation):
    ...


class VocabNote(Note):
    _word: str = Field()
    _meaning: str = Field()

    @property
    def word(self) -> str:
        return self._word

    @word.setter
    def word(self, value: str) -> None:
        self._word = value
        self._title = f'{value} (Vocab)'
        # set searchable text

    @property
    def meaning(self) -> str:
        return self._meaning

    @meaning.setter
    def meaning(self, value: str) -> None:
        self._meaning = value
        # set searchable text

    @property
    def synonyms(self):
        return self._parent_relations(Synonym)

    @property
    def antonyms(self):
        return self._parent_relations(Antonym)


class ResourceNote(Note):
    urls: Dict[str, ResourceNote] = ClassDictField()
    _mime: str = Field()
    _url: str = Field()
    _metadata: str = Field()

    def __init__(self):
        super().__init__()
        self._url = ''

    @property
    def mime(self) -> str:
        return self._mime

    @mime.setter
    def mime(self, value: str) -> None:
        self._mime = value
        # set searchable text

    @property
    def url(self) -> str:
        return self._url

    @url.setter
    def url(self, value: str) -> None:
        if not value:
            raise Exception('Invalid URL')
        if value == self._url:
            return
        if self._url:
            del ResourceNote.urls[self._url]
        ResourceNote.urls[value] = self
        self._url = value
        # set searchable text

    @property
    def metadata(self) -> str:
        return self._metadata

    @metadata.setter
    def metadata(self, value: str) -> None:
        self._metadata = value
        # set searchable text


class VideoRN(ResourceNote, ABC):
    pass


class YoutubeVRN(VideoRN):
    _captions: str = Field()
    _description: str = Field()

    @property
    def video_title(self) -> str:
        return self._title

    @video_title.setter
    def video_title(self, value: str) -> None:
        self._title = value
        # set searchable text here


if __name__ == '__main__':
    revert.connect('db')
    with Transaction():
        orphans = Shelf('orphans')
        python = MarkdownNote()
        python.content = 'Python'
    print(python.content)
    with Transaction():
        python.delete()
    print(python.content)
