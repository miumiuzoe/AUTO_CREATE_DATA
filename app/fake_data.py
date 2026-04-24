import ast
import random
import re
from typing import Any, List, Optional

from faker import Faker

from app import date_methods
from app.database import query_values
from app.models import FieldInfo


class FakeDataBuilder:
    def __init__(self, rules: dict, engine=None):
        self.rules = [_parse_rule(key, value) for key, value in rules.items()]
        self.faker = Faker("zh_CN")
        self.engine = engine

    def build_record(self, fields: List[FieldInfo]) -> str:
        values = [self.build_value(field) for field in fields]
        return "\t".join(values)

    def build_value(self, field: FieldInfo) -> str:
        for rule in self.rules:
            if rule["eng"] and rule["eng"] in field.iof_engname.upper():
                return self._resolve_rule_value(rule["value"])
            if rule["zh"] and rule["zh"] in field.iof_chiname:
                return self._resolve_rule_value(rule["value"])
        return ""

    def _resolve_rule_value(self, value: Any) -> str:
        if isinstance(value, list):
            if len(value) == 1 and isinstance(value[0], str) and _looks_like_sql(value[0]):
                return self._resolve_database_query(value[0])
            return str(self._resolve_rule_value(random.choice(value)))

        if isinstance(value, str):
            faker_result = _resolve_faker_value(value, self.faker)
            if faker_result is not None:
                return faker_result

            if _looks_like_sql(value):
                return self._resolve_database_query(value)

            internal_result = _resolve_internal_method_value(value)
            if internal_result is not None:
                return internal_result

            return value

        return str(value)

    def _resolve_database_query(self, sql_text: str) -> str:
        if self.engine is None:
            raise ValueError("fake.yml 中配置了数据库查询规则，但当前未提供数据库连接。")

        values = query_values(self.engine, sql_text)
        if not values:
            raise ValueError(f"数据库查询未返回任何结果: {sql_text}")
        return str(random.choice(values))


def _parse_rule(raw_key: str, value):
    match = re.match(r"^(.*?)\[(.*)\]$", raw_key)
    if match:
        eng = match.group(1).strip().upper()
        zh = match.group(2).strip()
    else:
        eng = raw_key.strip().upper()
        zh = ""
    return {"eng": eng, "zh": zh, "value": value}


def _looks_like_sql(value: str) -> bool:
    return value.strip().upper().startswith("SELECT ")


def _resolve_faker_value(rule: str, faker_obj: Faker) -> Optional[str]:
    match = re.fullmatch(r"faker\.([A-Za-z_][A-Za-z0-9_]*)\((.*)\)", rule.strip())
    if not match:
        return None

    method_name = match.group(1)
    if method_name == "phonenumber" and not match.group(2).strip():
        return faker_obj.numerify("1##########")

    if not hasattr(faker_obj, method_name):
        raise ValueError(f"fake.yml 中存在未知 faker 方法: {method_name}")

    method = getattr(faker_obj, method_name)
    args, kwargs = _parse_call_arguments(match.group(2))
    return str(method(*args, **kwargs))


def _resolve_internal_method_value(rule: str) -> Optional[str]:
    stripped = rule.strip()
    if not stripped.startswith("date_methods."):
        return None

    try:
        expression = ast.parse(stripped, mode="eval")
    except SyntaxError:
        return None

    if not _is_allowed_internal_expression(expression):
        raise ValueError(f"fake.yml 中存在不受支持的内部方法调用: {rule}")

    safe_globals = {"__builtins__": {}}
    safe_locals = {"date_methods": date_methods}
    return str(eval(compile(expression, "<fake_rule>", "eval"), safe_globals, safe_locals))


def _parse_call_arguments(raw_args: str):
    stripped = raw_args.strip()
    if not stripped:
        return [], {}

    expression = ast.parse(f"_func({stripped})", mode="eval")
    call_node = expression.body
    args = [ast.literal_eval(arg) for arg in call_node.args]
    kwargs = {keyword.arg: ast.literal_eval(keyword.value) for keyword in call_node.keywords}
    return args, kwargs


def _is_allowed_internal_expression(node: ast.AST) -> bool:
    allowed_nodes = (
        ast.Expression,
        ast.Call,
        ast.Name,
        ast.Load,
        ast.Constant,
        ast.Attribute,
        ast.List,
        ast.Tuple,
        ast.Dict,
        ast.keyword,
        ast.UnaryOp,
        ast.USub,
    )

    for child in ast.walk(node):
        if not isinstance(child, allowed_nodes):
            return False
        if isinstance(child, ast.Name) and child.id != "date_methods":
            return False
    return True
