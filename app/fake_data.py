import random
import re
from typing import List

from faker import Faker

from app.models import FieldInfo


class FakeDataBuilder:
    def __init__(self, rules: dict):
        self.rules = [_parse_rule(key, value) for key, value in rules.items()]
        self.faker = Faker("zh_CN")

    def build_record(self, fields: List[FieldInfo]) -> str:
        values = [self.build_value(field) for field in fields]
        return "\t".join(values)

    def build_value(self, field: FieldInfo) -> str:
        # 先按英文字段名匹配，再按中文字段名匹配，最后回退到默认值。
        for rule in self.rules:
            if rule["eng"] and rule["eng"] in field.iof_engname.upper():
                return _resolve_rule_value(rule["value"], self.faker)
            if rule["zh"] and rule["zh"] in field.iof_chiname:
                return _resolve_rule_value(rule["value"], self.faker)
        return f"{field.iof_id}_{field.iof_engname}"


def _parse_rule(raw_key: str, value):
    match = re.match(r"^(.*?)\[(.*)\]$", raw_key)
    if match:
        eng = match.group(1).strip().upper()
        zh = match.group(2).strip()
    else:
        eng = raw_key.strip().upper()
        zh = ""
    return {"eng": eng, "zh": zh, "value": value}


def _resolve_rule_value(value, faker_obj: Faker) -> str:
    if isinstance(value, list):
        return str(random.choice(value))

    if isinstance(value, str):
        faker_method = _get_faker_method(value, faker_obj)
        if faker_method:
            return str(faker_method())
        return value

    return str(value)


def _get_faker_method(rule: str, faker_obj: Faker):
    match = re.fullmatch(r"faker\.([A-Za-z_][A-Za-z0-9_]*)\(\)", rule.strip())
    if not match:
        return None

    method_name = match.group(1)
    if method_name == "phonenumber":
        return lambda: faker_obj.numerify("1##########")

    if not hasattr(faker_obj, method_name):
        raise ValueError(f"fake.yml 中存在未知 faker 方法: {method_name}")

    return getattr(faker_obj, method_name)
