from enum import Enum
from constants import ChoiceEnum
from typing import List, Type, Any, Callable, Union, Dict, Tuple, Set, FrozenSet
import json


class JSONable:
    def to_json(self):
        return to_json_object(self)

    def to_json_str(self):
        return json.dumps(self.to_json())
    
    def __str__(self) -> str:
        return self.to_json_str()

    def __repr__(self) -> str:
        return self.to_json_str()


class JEncoder(json.JSONEncoder):
    def default(self, o: Any) -> str:
        return to_json_object(o)


def get_encoder():
    return JEncoder


def get_decoder(clazz: Type[Any], **kwargs):
    class JDecoder(json.JSONDecoder):
        def decode(self, s: str, _w: Callable[..., Any] = ...) -> Union[JSONable, List]:
            jsn = super().decode(s, _w)

            if isinstance(jsn, list):
                return convert_list(jsn, clazz, **kwargs)
            return convert_object(jsn, clazz, **kwargs)

    return JDecoder


def convert_list(jsn_arr: list, clazz: Type[List[Any]], **kwargs) -> Union[List, None]:
    if jsn_arr is None:
        return None

    arr = []
    item_clazz = clazz.__args__[0]
    for jsn in jsn_arr:
        arr.append(convert_field(jsn, item_clazz))
    return arr


def convert_dict(jsn_dict: dict, clazz: Type[Dict[Any, Any]], **kwargs) -> Union[Dict, None]:
    if jsn_dict is None:
        return None

    dictionary = dict()
    k_clazz = clazz.__args__[0]
    v_clazz = clazz.__args__[1]
    for k, v in jsn_dict.items():
        dictionary[convert_field(k, k_clazz)] = convert_field(v, v_clazz)
    return dictionary


def convert_object(jsn: dict, clazz: Type[JSONable], **kwargs):
    """
    反序列化
    :param jsn:
    :param clazz:
    :return:
    """
    if jsn is None:
        return None

    obj = clazz()

    for k, v in clazz.__annotations__.items():
        val = convert_field(jsn.get(k), v)
        obj.__dict__[k] = val

    return obj


def convert_field(jsn, v):
    if jsn is None:
        return None

    if isinstance(v, type):
        if v in (str, int, float, bool, list, tuple, set, frozenset):
            return jsn
        elif issubclass(v, ChoiceEnum):
            ce = v.code_of(jsn)
            if not ce:
                ce = v(jsn)
            return ce
        elif issubclass(v, Enum):
            return v(jsn)
    elif __is_generic_alias(v, List, Tuple, Set, FrozenSet):
        return convert_list(jsn, v)
    elif __is_generic_alias(v, Dict):
        return convert_dict(jsn, v)

    return convert_object(jsn, v)

def j(obj):
    if isinstance(obj, JSONable):
        return obj.to_json()
    return to_json_object(obj)


def to_json_object(obj):
    if obj is None:
        return None

    obj_type = type(obj)

    if obj_type in (str, int, float, bool):
        return obj
    elif issubclass(obj_type, ChoiceEnum):
        return obj.code()
    elif issubclass(obj_type, Enum):
        return obj.name
    elif obj_type in (set, list, tuple, frozenset):
        return [j(i) for i in obj]
    elif obj_type == dict or __is_generic_alias(obj_type, Dict):
        return dict((j(k), j(v)) for k, v in obj.items())
    else:
        # 双下划线开头的值不序列化
        return dict((j(k), j(v))
                    for k, v in obj.__dict__.items() if not is_protected_attr(str(k), type(obj).__name__))


def is_protected_attr(k_str: str, class_name):
    return k_str.startswith('__') or k_str.startswith(f"_{class_name}__")


def __is_generic_alias(t, *gas):
    if not isinstance(t, Type.__class__):
        return False

    if len(gas) == 0:
        return True

    for ga in gas:
        if t.__origin__ == ga.__origin__:
            return True
    return False
