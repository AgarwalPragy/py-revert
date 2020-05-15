from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Iterable, Optional, Type, TypeVar

from revert import Transaction
from . import config
from .collections import Dict, ProtectedSet

__all__ = ['Edge', 'Node', 'DirectedEdge', 'UndirectedEdge', 'data']

T = TypeVar('T')
TNode = TypeVar('TNode', bound='Node')


# todo: reset revert to a normal ORM. Remove the graph thing and make it in the model itself

def clone(obj: T) -> T:
    copy = object.__new__(obj.__class__)
    copy.__dict__ = obj.__dict__.copy()
    return copy


class Edge(ABC):
    @classmethod
    def class_reference(cls: Type[Edge]) -> str:
        return f'{cls.__qualname__}'

    @abstractmethod
    def delete(self):
        ...


def get_uid(node: Node) -> str:
    return str(object.__getattribute__(node, '__uid__'))


class DirectedEdge(Edge, ABC):
    @property
    def parent(self) -> Node:
        return object.__getattribute__(self, '__parent__')

    @property
    def child(self) -> Node:
        return object.__getattribute__(self, '__child__')

    @classmethod
    def __init_subclass__(cls, **kwargs):
        ogm.register_edge_class(cls)

    def __init__(self, *, parent: Node, child: Node) -> None:
        actual_cls = self.__class__.class_reference()
        for cls in self.__class__.mro():
            if issubclass(cls, Edge):
                Transaction.count_up_or_set(f'{config.base}/child_relations/{get_uid(parent)}/{cls.class_reference()}/{get_uid(child)}')
                Transaction.count_up_or_set(f'{config.base}/parent_relations/{get_uid(child)}/{cls.class_reference()}/{get_uid(parent)}')
                Transaction.set(f'{config.base}/child_edges/{get_uid(parent)}/{get_uid(child)}/{cls.class_reference()}/{actual_cls}', '')
                Transaction.set(f'{config.base}/parent_edges/{get_uid(child)}/{get_uid(parent)}/{cls.class_reference()}/{actual_cls}', '')

    def delete(self) -> None:
        actual_cls = self.__class__.class_reference()
        for cls in self.__class__.mro():
            if issubclass(cls, Edge):
                Transaction.count_down_or_del(f'{config.base}/child_relations/{get_uid(self.parent)}/{cls.class_reference()}/{get_uid(self.child)}')
                Transaction.count_down_or_del(f'{config.base}/parent_relations/{get_uid(self.child)}/{cls.class_reference()}/{get_uid(self.parent)}')
                Transaction.delete(f'{config.base}/child_edges/{get_uid(self.parent)}/{get_uid(self.child)}/{cls.class_reference()}/{actual_cls}')
                Transaction.delete(f'{config.base}/parent_edges/{get_uid(self.child)}/{get_uid(self.parent)}/{cls.class_reference()}/{actual_cls}')

    def __hash__(self) -> int:
        return hash((self.__class__, self.parent, self.child))

    def __eq__(self, other: Any) -> bool:
        return self is other or (self.__class__ == other.__class__ and self.parent == other.parent and self.child == other.child)


class UndirectedEdge(Edge, ABC):
    @property
    def node_1(self) -> Node:
        return object.__getattribute__(self, '__node_1__')

    @property
    def node_2(self) -> Node:
        return object.__getattribute__(self, '__node_2__')

    @classmethod
    def __init_subclass__(cls, **kwargs):
        ogm.register_edge_class(cls)

    def __init__(self, *, node_1: Node, node_2: Node) -> None:
        actual_cls = self.__class__.class_reference()
        for cls in self.__class__.mro():
            if issubclass(cls, Edge):
                Transaction.count_up_or_set(f'{config.base}/parent_relations/{get_uid(node_1)}/{cls.class_reference()}/{get_uid(node_2)}')
                Transaction.count_up_or_set(f'{config.base}/child_relations/{get_uid(node_1)}/{cls.class_reference()}/{get_uid(node_2)}')
                Transaction.count_up_or_set(f'{config.base}/parent_relations/{get_uid(node_2)}/{cls.class_reference()}/{get_uid(node_1)}')
                Transaction.count_up_or_set(f'{config.base}/child_relations/{get_uid(node_2)}/{cls.class_reference()}/{get_uid(node_1)}')
                Transaction.set(f'{config.base}/bi_edges/{get_uid(node_1)}/{get_uid(node_2)}/{cls.class_reference()}/{actual_cls}', '')
                Transaction.set(f'{config.base}/bi_edges/{get_uid(node_2)}/{get_uid(node_1)}/{cls.class_reference()}/{actual_cls}', '')

    def delete(self) -> None:
        actual_cls = self.__class__.class_reference()
        for cls in self.__class__.mro():
            if issubclass(cls, Edge):
                Transaction.count_down_or_del(f'{config.base}/parent_relations/{get_uid(self.node_1)}/{cls.class_reference()}/{get_uid(self.node_2)}')
                Transaction.count_down_or_del(f'{config.base}/child_relations/{get_uid(self.node_1)}/{cls.class_reference()}/{get_uid(self.node_2)}')
                Transaction.count_down_or_del(f'{config.base}/parent_relations/{get_uid(self.node_2)}/{cls.class_reference()}/{get_uid(self.node_1)}')
                Transaction.count_down_or_del(f'{config.base}/child_relations/{get_uid(self.node_2)}/{cls.class_reference()}/{get_uid(self.node_1)}')
                Transaction.delete(f'{config.base}/bi_edges/{get_uid(self.node_1)}/{get_uid(self.node_2)}/{cls.class_reference()}/{actual_cls}')
                Transaction.delete(f'{config.base}/bi_edges/{get_uid(self.node_2)}/{get_uid(self.node_1)}/{cls.class_reference()}/{actual_cls}')

    def __hash__(self) -> int:
        return hash((self.__class__, self.node_1, self.node_2))

    def __eq__(self, other: Any) -> bool:
        return self is other or (self.__class__ == other.__class__ and self.node_1 == other.node_1 and self.node_2 == other.node_2)


class Node:
    @property
    def uid(self) -> str:
        return object.__getattribute__(self, '__uid__')

    @property
    def created_at(self) -> datetime:
        return object.__getattribute__(self, '__created_at__')

    @property
    def updated_at(self) -> datetime:
        return object.__getattribute__(self, '__updated_at__')

    def delete(self) -> None:
        for edge in set(self.edges()):
            edge.delete()
        ogm.delete_node(self)

    def _parent_relations(self, edge_type: Type[Edge]) -> ProtectedSet[Node]:
        return ProtectedSet(__binding__=f'{config.base}/parent_relations/{get_uid(self)}/{edge_type.class_reference()}/')

    def _child_relations(self, edge_type: Type[Edge]) -> ProtectedSet[Node]:
        return ProtectedSet(__binding__=f'{config.base}/child_relations/{get_uid(self)}/{edge_type.class_reference()}/')

    def edges(self, with_node: Optional[Node] = None, edge_type: Optional[Type[Edge]] = None) -> Iterable[Edge]:
        if edge_type is None:
            edge_type = Edge
        if with_node is None:
            for key in Transaction.match_keys(f'{config.base}/parent_edges/{get_uid(self)}/'):
                with_node = ogm.get_node(key.split('/')[3])
                yield from self.edges(with_node)
            for key in Transaction.match_keys(f'{config.base}/child_edges/{get_uid(self)}/'):
                with_node = ogm.get_node(key.split('/')[3])
                yield from self.edges(with_node)
            for key in Transaction.match_keys(f'{config.base}/bi_edges/{get_uid(self)}/'):
                with_node = ogm.get_node(key.split('/')[3])
                yield from self.edges(with_node)
            return
        for key in Transaction.match_keys(f'{config.base}/parent_edges/{get_uid(self)}/{get_uid(with_node)}/{edge_type.class_reference()}/'):
            cls: Type[Edge] = ogm.edge_classes[key.split('/')[-1].strip()]
            edge: Edge = object.__new__(cls)
            object.__setattr__(edge, '__parent__', self)
            object.__setattr__(edge, '__child__', with_node)
            yield edge
        for key in Transaction.match_keys(f'{config.base}/child_edges/{get_uid(self)}/{get_uid(with_node)}/{edge_type.class_reference()}/'):
            cls: Type[Edge] = ogm.edge_classes[key.split('/')[-1].strip()]
            edge: Edge = object.__new__(cls)
            object.__setattr__(edge, '__parent__', with_node)
            object.__setattr__(edge, '__child__', edge)
            yield edge
        for key in Transaction.match_keys(f'{config.base}/bi_edges/{get_uid(self)}/{get_uid(with_node)}/{edge_type.class_reference()}/'):
            cls: Type[Edge] = ogm.edge_classes[key.split('/')[-1].strip()]
            edge: Edge = object.__new__(cls)
            object.__setattr__(edge, '__node_1__', self)
            object.__setattr__(edge, '__node_2__', with_node)
            yield edge

    @classmethod
    def __init_subclass__(cls, **kwargs):
        ogm.register_node_class(cls)

    def __new__(cls, *args, **kwargs):
        if cls == Node:
            raise TypeError('Cannot create objects of abstract Node class')
        obj = object.__new__(cls)
        ogm.register_node(obj)
        return obj

    def __repr__(self):
        return f'{self.__class__.__qualname__}.get_instance(\'{object.__getattribute__(self, "__uid__")}\')'

    def __eq__(self, other: Any) -> bool:
        return self is other or (isinstance(other, Node) and object.__getattribute__(self, '__uid__') == object.__getattribute__(other, '__uid__'))

    def __hash__(self):
        return hash(object.__getattribute__(self, '__uid__'))

    @classmethod
    def class_reference(cls: Type[Node]) -> str:
        return f'{cls.__qualname__}'


data: Dict


def __getattr__(name: str):
    if name == 'data':
        return Dict(__binding__='')


from . import ogm
