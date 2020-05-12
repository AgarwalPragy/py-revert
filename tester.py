from __future__ import annotations

from abc import ABC
from typing import Set, TypeVar

from revert.graph import DirectedEdge, Field, Node, ProtectedSet, SetField, UndirectedEdge

T = TypeVar('T')


class TF_IDF:
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


class Note(Node, ABC):
    _stats: NoteStats = Field()
    access_level: str = Field()
    shelves: Set[Shelf] = SetField()  # todo: should this be a set or an edge?

    _search_index: TF_IDF = Field()
    _title: str = Field()

    def __init__(self):
        self._stats = NoteStats(self)

    def delete(self):
        for edge in list(self.edges()):
            edge.delete()
        self._stats.delete()
        for shelf in self.shelves:
            shelf.notes.discard(self)
        super().delete()

    @property
    def stats(self) -> NoteStats:
        return self._stats

    @property
    def sources(self) -> ProtectedSet[Note]:
        return self._parent_relations(Source)

    @property
    def extracted(self) -> Set[Note]:
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
    votes: int = Field()
    _name: str = UniqueField()
    notes: Set[Note] = SetField()

    def __init__(self, name: str) -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def add_note(self, note: Note) -> None:
        self.notes.add(note)
        note.shelves.add(self)

    def delete(self):
        for note in self.notes:
            note.shelves.discard(self)


class Source(DirectedEdge):
    def __init__(self, note: Note, source: Note) -> None:
        super().__init__(parent=source, child=note)


class Reference(DirectedEdge):
    def __init__(self, note: Note, reference: Note) -> None:
        super().__init__(parent=note, child=reference)


class Tag(DirectedEdge):
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


class Synonym(UndirectedEdge):
    ...


class Antonym(UndirectedEdge):
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


class ResourceNote(Note, ABC):
    _mime: str = Field()
    _url: str = UniqueField()  # todo: enforce by attaching attribs to class and using that class data to check for uniqueness
    # todo: add index on url
    _metadata: str = Field()

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
