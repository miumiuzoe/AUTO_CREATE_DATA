from typing import Any, Dict, List

from sqlalchemy import URL, create_engine, text

from app.models import DatabaseConfig, FieldInfo, ProtocolOption


def build_engine(config: DatabaseConfig):
    db_type = config.db_type.lower()

    if db_type == "mysql":
        driver = "mysql+pymysql"
    elif db_type in ("postgresql", "postgres"):
        driver = "postgresql+pg8000"
    elif db_type == "oracle":
        driver = "oracle+oracledb"
    else:
        raise ValueError(f"不支持的数据库类型: {config.db_type}")

    url = URL.create(
        drivername=driver,
        username=config.username,
        password=config.password,
        host=config.host,
        port=config.port,
        database=config.database,
    )
    return create_engine(url)


def query_protocols(engine, sql_text: str, protocol_name: str) -> List[ProtocolOption]:
    rows = _query(engine, sql_text, {"obj_engname": protocol_name})
    if not rows:
        raise ValueError(f"未找到协议: {protocol_name}")

    result = []
    for row in rows:
        data = {str(key).upper(): value for key, value in row.items()}
        if "OBJ_GUID" not in data:
            raise ValueError("协议查询结果中缺少 OBJ_GUID 字段。")
        if "SYS_ID" not in data:
            raise ValueError("协议查询结果中缺少 SYS_ID 字段。")

        result.append(
            ProtocolOption(
                obj_guid=str(data["OBJ_GUID"]),
                sys_id=str(data["SYS_ID"]),
                data=data,
            )
        )
    return result


def query_fields(engine, sql_text: str, obj_guid: str, obj_engname: str) -> List[FieldInfo]:
    rows = _query(engine, sql_text, {"obj_guid": obj_guid, "obj_engname": obj_engname})
    if not rows:
        raise ValueError(f"未找到 OBJ_GUID={obj_guid} 对应的协议字段。")

    result = []
    for row in rows:
        data = {str(key).upper(): value for key, value in row.items()}
        result.append(
            FieldInfo(
                iof_id=int(data["IOF_ID"]),
                iof_engname=str(data["IOF_ENGNAME"]),
                iof_chiname=str(data.get("IOF_CHINAME", "")),
            )
        )
    return sorted(result, key=lambda item: item.iof_id)


def query_values(engine, sql_text: str) -> List[Any]:
    rows = _query(engine, sql_text, {})
    values = []
    for row in rows:
        if row:
            values.append(next(iter(row.values())))
    return values


def _query(engine, sql_text: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    with engine.begin() as connection:
        result = connection.execute(text(sql_text), params)
        return [dict(row._mapping) for row in result]
