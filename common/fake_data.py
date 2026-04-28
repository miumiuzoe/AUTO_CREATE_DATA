import ast
import random
import re
from typing import Any, List, Optional

from faker import Faker

from common import date_methods
from common.database import query_values
from common.models import FieldInfo


class FakeDataBuilder:
    """根据字段元数据和 fake.yml 规则生成 Tab 分隔的 BCP 记录。"""

    def __init__(self, rules: dict, engine=None):
        """解析假数据规则，并保存可选的数据库连接引擎。"""
        self.rules = [_parse_rule(key, value) for key, value in rules.items()]
        self.faker = Faker("zh_CN")
        self.engine = engine

    def build_record(self, fields: List[FieldInfo]) -> str:
        """按协议字段顺序生成一条 Tab 分隔记录。"""
        values = [self.build_value(field) for field in fields]
        return "\t".join(values)

    def build_value(self, field: FieldInfo) -> str:
        """根据 fake.yml 规则生成单个字段值。"""
        for rule in self.rules:
            if rule["eng"] and rule["eng"] == field.iof_engname.upper():
                return self._resolve_rule_value(rule["value"])
            if rule["zh"] and rule["zh"] in field.iof_chiname:
                return self._resolve_rule_value(rule["value"])
        return ""

    def _resolve_rule_value(self, value: Any) -> str:
        """将配置中的规则值解析为最终输出字符串。"""
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
        """执行 SQL 类型假数据规则，并从返回值中随机取一个。"""
        if self.engine is None:
            raise ValueError("fake.yml 中配置了 SQL 规则，但当前未提供数据库连接。")

        values = query_values(self.engine, sql_text)
        if not values:
            raise ValueError(f"数据库规则未返回任何值: {sql_text}")
        return str(random.choice(values))


def _parse_rule(raw_key: str, value):
    """将 fake.yml 的规则 key 解析为英文名和中文名匹配条件。"""
    match = re.match(r"^(.*?)\[(.*)\]$", raw_key)
    if match:
        eng = match.group(1).strip().upper()
        zh = match.group(2).strip()
    else:
        eng = raw_key.strip().upper()
        zh = ""
    return {"eng": eng, "zh": zh, "value": value}


def _looks_like_sql(value: str) -> bool:
    """判断字符串是否应按 SQL 查询规则处理。"""
    return value.strip().upper().startswith("SELECT ")


def _resolve_faker_value(rule: str, faker_obj: Faker) -> Optional[str]:
    """解析 faker.method(...) 规则，不是 faker 规则时返回 None。"""
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
    """解析允许调用的内部 date_methods.* 规则。"""
    stripped = rule.strip()
    if not stripped.startswith("date_methods."):
        return None

    try:
        expression = ast.parse(stripped, mode="eval")
    except SyntaxError:
        return None

    if not _is_allowed_internal_expression(expression):
        raise ValueError(f"fake.yml 中存在不支持的内部方法调用: {rule}")

    safe_globals = {"__builtins__": {}}
    safe_locals = {"date_methods": date_methods}
    return str(eval(compile(expression, "<fake_rule>", "eval"), safe_globals, safe_locals))


def _parse_call_arguments(raw_args: str):
    """解析规则调用中的字面量位置参数和关键字参数。"""
    stripped = raw_args.strip()
    if not stripped:
        return [], {}

    expression = ast.parse(f"_func({stripped})", mode="eval")
    call_node = expression.body
    args = [ast.literal_eval(arg) for arg in call_node.args]
    kwargs = {keyword.arg: ast.literal_eval(keyword.value) for keyword in call_node.keywords}
    return args, kwargs


def _is_allowed_internal_expression(node: ast.AST) -> bool:
    """校验内部方法规则表达式只包含允许的 AST 节点。"""
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
