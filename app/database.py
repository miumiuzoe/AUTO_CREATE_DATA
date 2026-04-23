from typing import Dict, List

from sqlalchemy import create_engine, text

from app.models import DatabaseConfig, FieldInfo


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

    url = (
        f"{driver}://{config.username}:{config.password}"
        f"@{config.host}:{config.port}/{config.database}"
    )
    return create_engine(url)


def query_fields(engine, sql_text: str, protocol_name: str) -> List[FieldInfo]:
    rows = _query(engine, sql_text, protocol_name)
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


def query_sys_id(engine, sql_text: str, protocol_name: str) -> str:
    rows = _query(engine, sql_text, protocol_name)
    if not rows:
        raise ValueError("未查询到 SYS_ID。")
    data = {str(key).upper(): value for key, value in rows[0].items()}
    return str(data["SYS_ID"])


def _query(engine, sql_text: str, protocol_name: str) -> List[Dict]:
    with engine.begin() as connection:
        result = connection.execute(text(sql_text), {"obj_engname": protocol_name})
        return [dict(row._mapping) for row in result]
