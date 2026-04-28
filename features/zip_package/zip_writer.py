import random
import time
import zipfile
from io import BytesIO
from pathlib import Path
from typing import List
from xml.etree import ElementTree

from common.models import FieldInfo, ZipBinaryEntry


def build_zip_name(sys_id: str) -> str:
    """生成标准 ZIP 压缩包文件名。"""
    timestamp = str(int(time.time()))
    random_code = random.randint(10000, 99999)
    return f"{sys_id}-330000-330000-{timestamp}-{random_code}.zip"


def write_zip_package(
    output_dir: Path,
    template_path: Path,
    protocol_name: str,
    sys_id: str,
    bcp_file_name: str,
    bcp_content: str,
    fields: List[FieldInfo],
    zip_entries: List[ZipBinaryEntry],
) -> Path:
    """写入只包含内存中 BCP 文件和 XML 文件的 ZIP 压缩包。"""
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / build_zip_name(sys_id)
    xml_content = build_zip_xml(template_path, protocol_name, sys_id, bcp_file_name, fields)

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr(bcp_file_name, bcp_content + "\n")
        zip_file.writestr(template_path.name, xml_content)
        for entry in zip_entries:
            zip_file.writestr(entry.relative_path.as_posix(), entry.content)

    return zip_path


def build_zip_xml(
    template_path: Path,
    protocol_name: str,
    sys_id: str,
    bcp_file_name: str,
    fields: List[FieldInfo],
) -> bytes:
    """根据 XML 模板和协议字段信息生成 ZIP 内 XML 内容。"""
    tree = ElementTree.parse(template_path)
    root = tree.getroot()

    _set_item_val(root, "01A0004", protocol_name)
    _set_item_val(root, "01A0005", sys_id)
    _set_item_val(root, "01A0006", bcp_file_name)
    _replace_common_dataset_items(root, fields)

    _indent_xml(root)
    output = BytesIO()
    tree.write(output, encoding="utf-8", xml_declaration=True)
    return output.getvalue()


def _set_item_val(root: ElementTree.Element, key: str, value: str) -> None:
    """设置第一个指定 key 的 ITEM 节点 val 属性。"""
    for item in root.iter("ITEM"):
        if item.get("key") == key:
            item.set("val", value)
            return
    raise ValueError(f"template/zip.xml 中缺少 ITEM key={key}")


def _replace_common_dataset_items(root: ElementTree.Element, fields: List[FieldInfo]) -> None:
    """替换 DATASET COMMON_0015 下 DATA 节点中的字段 ITEM。"""
    data_node = _find_common_dataset_data(root)
    for child in list(data_node):
        data_node.remove(child)
    data_node.text = None

    for field in fields:
        ElementTree.SubElement(
            data_node,
            "ITEM",
            {
                "key": field.iof_keyname,
                "eng": field.iof_engname,
                "chn": field.iof_chiname,
            },
        )


def _find_common_dataset_data(root: ElementTree.Element) -> ElementTree.Element:
    """查找或创建 DATASET name=COMMON_0015 下的 DATA 节点。"""
    for dataset in root.iter("DATASET"):
        if dataset.get("name") != "COMMON_0015":
            continue

        for child in dataset:
            if child.tag == "DATA":
                return child

        return ElementTree.SubElement(dataset, "DATA")

    raise ValueError('template/zip.xml 中缺少 DATASET name="COMMON_0015"')


def _indent_xml(element: ElementTree.Element, level: int = 0) -> None:
    """原地为 XML 节点补充缩进空白，便于阅读。"""
    indent = "\n" + level * "  "
    child_indent = "\n" + (level + 1) * "  "
    children = list(element)

    if children:
        if not element.text or not element.text.strip():
            element.text = child_indent
        for child in children:
            _indent_xml(child, level + 1)
        if not children[-1].tail or not children[-1].tail.strip():
            children[-1].tail = indent

    if level and (not element.tail or not element.tail.strip()):
        element.tail = indent
