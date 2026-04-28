import math
import random
import shutil
import subprocess
import tempfile
import time
import wave
from email.message import EmailMessage
from io import BytesIO
from pathlib import Path
from typing import Optional

from faker import Faker

from common.models import GeneratedFieldValue, ZipBinaryEntry
from common.paths import DEFAULT_SPECIAL_CHARS, build_random_relative_dir_path


faker = Faker("zh_CN")

TEXT_TYPE = "text"
WEB_TYPE = "web"
EMAIL_TYPE = "email"
IMAGE_TYPE = "image"
AUDIO_TYPE = "audio"
VIDEO_TYPE = "video"

DEFAULT_SIZE_HINT_KB = 16


def generate_random_unstructured_file(
    output_dir: Path,
    data_type: str,
    file_name: Optional[str] = None,
    size_hint_kb: int = DEFAULT_SIZE_HINT_KB,
    image_format: str = "svg",
    video_format: str = "y4m",
) -> Path:
    """生成随机非结构化文件到磁盘，并返回文件路径。"""
    file_name = file_name or _resolve_file_name(data_type, None, image_format, video_format)
    generated = generate_zip_unstructured_value(
        data_type=data_type,
        file_name=file_name,
        size_hint_kb=size_hint_kb,
        image_format=image_format,
        video_format=video_format,
        directory_levels=0,
    )
    target_path = output_dir / generated.field_value
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(generated.zip_entries[0].content)
    return target_path


def generate_zip_unstructured_value(
    data_type: str,
    file_name: Optional[str] = None,
    size_hint_kb: int = DEFAULT_SIZE_HINT_KB,
    image_format: str = "svg",
    video_format: str = "y4m",
    directory_levels: int = 0,
    directory_levels_list: Optional[list[int]] = None,
    dir_name_length: int = 8,
    dir_special_chars: str = DEFAULT_SPECIAL_CHARS,
    file_count: int = 1,
    separator: str = ";",
) -> GeneratedFieldValue:
    """生成 ZIP 内文件条目，并返回应写入字段的相对路径值。"""
    if size_hint_kb <= 0:
        raise ValueError("size_hint_kb 必须大于 0。")
    if file_count <= 0:
        raise ValueError("file_count 必须大于 0。")
    if directory_levels_list is not None:
        if len(directory_levels_list) != file_count:
            raise ValueError("directory_levels_list 的长度必须与 file_count 一致。")
        if any(level < 0 for level in directory_levels_list):
            raise ValueError("directory_levels_list 中的层级不能小于 0。")

    normalized_type = data_type.strip().lower()
    normalized_image_format = image_format.strip().lower()
    normalized_video_format = video_format.strip().lower()
    field_values = []
    zip_entries = []

    for index in range(file_count):
        current_directory_levels = (
            directory_levels_list[index] if directory_levels_list is not None else directory_levels
        )
        relative_dir = build_random_relative_dir_path(
            levels=current_directory_levels,
            name_length=dir_name_length,
            special_chars=dir_special_chars,
        )
        resolved_name = _resolve_file_name(
            normalized_type,
            _resolve_indexed_file_name(file_name, index, file_count),
            normalized_image_format,
            normalized_video_format,
        )
        relative_path = relative_dir / resolved_name if str(relative_dir) else Path(resolved_name)
        content = _build_unstructured_bytes(
            normalized_type,
            size_hint_kb,
            normalized_image_format,
            normalized_video_format,
        )
        field_values.append(relative_path.as_posix())
        zip_entries.append(ZipBinaryEntry(relative_path=relative_path, content=content))

    return GeneratedFieldValue(
        field_value=separator.join(field_values),
        zip_entries=zip_entries,
    )


def _build_unstructured_bytes(
    data_type: str,
    size_hint_kb: int,
    image_format: str,
    video_format: str,
) -> bytes:
    """按数据类型分派到对应的字节内容生成函数。"""
    if data_type == TEXT_TYPE:
        return _build_text_bytes(size_hint_kb)
    if data_type == WEB_TYPE:
        return _build_web_bytes(size_hint_kb)
    if data_type == EMAIL_TYPE:
        return _build_email_bytes(size_hint_kb)
    if data_type == IMAGE_TYPE:
        return _build_image_bytes(size_hint_kb, image_format)
    if data_type == AUDIO_TYPE:
        return _build_audio_bytes(size_hint_kb)
    if data_type == VIDEO_TYPE:
        return _build_video_bytes(size_hint_kb, video_format)

    supported = ", ".join(sorted((AUDIO_TYPE, EMAIL_TYPE, IMAGE_TYPE, TEXT_TYPE, VIDEO_TYPE, WEB_TYPE)))
    raise ValueError(f"不支持的非结构化数据类型: {data_type}，支持类型: {supported}")


def _resolve_file_name(
    data_type: str,
    file_name: Optional[str],
    image_format: str,
    video_format: str,
) -> str:
    """返回最终文件名；未显式指定时按类型自动补扩展名。"""
    if file_name:
        return file_name

    extension_map = {
        TEXT_TYPE: ".txt",
        WEB_TYPE: ".html",
        EMAIL_TYPE: ".eml",
        IMAGE_TYPE: f".{image_format}",
        AUDIO_TYPE: ".wav",
        VIDEO_TYPE: f".{video_format}",
    }
    timestamp = int(time.time())
    random_code = random.randint(1000, 9999)
    base_name = faker.word(ext_word_list=["record", "sample", "message", "asset", "content", "media"])
    return f"{base_name}_{timestamp}_{random_code}{extension_map[data_type]}"


def _resolve_indexed_file_name(file_name: Optional[str], index: int, file_count: int) -> Optional[str]:
    """批量生成多个文件时，为后续文件名追加序号后缀。"""
    if not file_name or file_count == 1:
        return file_name

    path = Path(file_name)
    suffix = "".join(path.suffixes)
    stem = path.name[: -len(suffix)] if suffix else path.name
    indexed_name = f"{stem}_{index + 1}{suffix}"
    return str(path.with_name(indexed_name))


def _build_text_bytes(size_hint_kb: int) -> bytes:
    """生成接近指定大小的随机文本内容。"""
    target_bytes = size_hint_kb * 1024
    chunks = []

    while len("".join(chunks).encode("utf-8")) < target_bytes:
        chunks.append(faker.paragraph(nb_sentences=random.randint(3, 7)))
        chunks.append("\n\n")

    return "".join(chunks).encode("utf-8")


def _build_web_bytes(size_hint_kb: int) -> bytes:
    """生成简单 HTML 页面内容。"""
    title = faker.sentence(nb_words=4).strip("。")
    sections = []
    target_bytes = size_hint_kb * 1024

    while len("".join(sections).encode("utf-8")) < max(target_bytes - 512, 256):
        heading = faker.sentence(nb_words=random.randint(2, 5)).strip("。")
        paragraph = "".join(
            f"<p>{faker.paragraph(nb_sentences=random.randint(3, 6))}</p>"
            for _ in range(random.randint(1, 3))
        )
        sections.append(f"<section><h2>{heading}</h2>{paragraph}</section>")

    html = (
        "<!DOCTYPE html>\n"
        "<html lang=\"zh-CN\">\n"
        "<head>\n"
        "  <meta charset=\"UTF-8\">\n"
        f"  <title>{title}</title>\n"
        "</head>\n"
        "<body>\n"
        f"  <h1>{title}</h1>\n"
        f"  {''.join(sections)}\n"
        "</body>\n"
        "</html>\n"
    )
    return html.encode("utf-8")


def _build_email_bytes(size_hint_kb: int) -> bytes:
    """生成 EML 格式的邮件内容。"""
    message = EmailMessage()
    message["From"] = faker.email()
    message["To"] = faker.email()
    message["Subject"] = faker.sentence(nb_words=6).strip("。")

    body_parts = []
    target_bytes = size_hint_kb * 1024
    while len("\n".join(body_parts).encode("utf-8")) < max(target_bytes - 512, 256):
        body_parts.append(faker.paragraph(nb_sentences=random.randint(3, 6)))

    message.set_content("\n\n".join(body_parts))
    return message.as_bytes()


def _build_image_bytes(size_hint_kb: int, image_format: str) -> bytes:
    """按图片格式生成 SVG 或位图图片字节。"""
    if image_format == "svg":
        return _build_svg_image_bytes(size_hint_kb)
    if image_format not in ("png", "jpg", "jpeg"):
        raise ValueError(f"不支持的图片格式: {image_format}，支持格式: svg, png, jpg, jpeg")
    return _build_raster_image_bytes(size_hint_kb, image_format)


def _build_svg_image_bytes(size_hint_kb: int) -> bytes:
    """生成随机 SVG 图形内容。"""
    width = random.choice((640, 800, 1024))
    height = random.choice((480, 600, 768))
    element_count = max(6, size_hint_kb)
    shapes = []

    for _ in range(element_count):
        color = _random_hex_color()
        opacity = random.uniform(0.25, 0.95)
        x = random.randint(0, width)
        y = random.randint(0, height)
        shape_type = random.choice(("circle", "rect", "line"))

        if shape_type == "circle":
            radius = random.randint(12, min(width, height) // 6)
            shapes.append(
                f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{color}" fill-opacity="{opacity:.2f}" />'
            )
        elif shape_type == "rect":
            rect_width = random.randint(20, width // 3)
            rect_height = random.randint(20, height // 3)
            shapes.append(
                f'<rect x="{max(0, x - rect_width // 2)}" y="{max(0, y - rect_height // 2)}" '
                f'width="{rect_width}" height="{rect_height}" fill="{color}" fill-opacity="{opacity:.2f}" />'
            )
        else:
            x2 = random.randint(0, width)
            y2 = random.randint(0, height)
            stroke_width = random.randint(1, 6)
            shapes.append(
                f'<line x1="{x}" y1="{y}" x2="{x2}" y2="{y2}" stroke="{color}" '
                f'stroke-width="{stroke_width}" stroke-opacity="{opacity:.2f}" />'
            )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n'
        f'  <rect width="{width}" height="{height}" fill="{_random_hex_color()}" fill-opacity="0.08" />\n'
        f"  {' '.join(shapes)}\n"
        "</svg>\n"
    )
    return svg.encode("utf-8")


def _build_raster_image_bytes(size_hint_kb: int, image_format: str) -> bytes:
    """使用 Pillow 生成 PNG/JPG/JPEG 位图内容。"""
    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise ValueError("生成 png/jpg/jpeg 图片需要先安装 Pillow。") from exc

    width = random.choice((640, 800, 1024))
    height = random.choice((480, 600, 768))
    image = Image.new("RGB", (width, height), _random_rgb_color())
    draw = ImageDraw.Draw(image, "RGBA")
    element_count = max(12, size_hint_kb * 2)

    for _ in range(element_count):
        color = _random_rgba_color()
        shape_type = random.choice(("ellipse", "rectangle", "line"))
        x1 = random.randint(0, width - 1)
        y1 = random.randint(0, height - 1)
        x2 = random.randint(0, width - 1)
        y2 = random.randint(0, height - 1)
        left, right = sorted((x1, x2))
        top, bottom = sorted((y1, y2))

        if shape_type == "ellipse":
            draw.ellipse((left, top, max(left + 1, right), max(top + 1, bottom)), fill=color)
        elif shape_type == "rectangle":
            draw.rectangle((left, top, max(left + 1, right), max(top + 1, bottom)), fill=color)
        else:
            draw.line((x1, y1, x2, y2), fill=color, width=random.randint(1, 6))

    output = BytesIO()
    save_format = "JPEG" if image_format in ("jpg", "jpeg") else "PNG"
    image.save(output, format=save_format)
    return output.getvalue()


def _build_audio_bytes(size_hint_kb: int) -> bytes:
    """生成 WAV 格式的随机音频内容。"""
    sample_rate = 16000
    sample_width = 2
    channels = 1
    target_bytes = size_hint_kb * 1024
    frame_count = max(8000, target_bytes // sample_width)
    amplitude = 16000
    freq1 = random.choice((220, 330, 440, 523, 659))
    freq2 = random.choice((110, 165, 262, 349))

    output = BytesIO()
    with wave.open(output, "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)

        frames = bytearray()
        for index in range(frame_count):
            value = int(
                amplitude * 0.6 * math.sin(2 * math.pi * freq1 * index / sample_rate)
                + amplitude * 0.4 * math.sin(2 * math.pi * freq2 * index / sample_rate)
            )
            frames.extend(value.to_bytes(2, byteorder="little", signed=True))

        wav_file.writeframes(bytes(frames))

    return output.getvalue()


def _build_video_bytes(size_hint_kb: int, video_format: str) -> bytes:
    """按视频格式生成原始 Y4M 或转码后的视频字节。"""
    if video_format == "y4m":
        return _build_y4m_video_bytes(size_hint_kb)
    if video_format not in ("mp4", "mkv", "mov", "wmv", "avi"):
        raise ValueError(f"不支持的视频格式: {video_format}，支持格式: y4m, mp4, mkv, mov, wmv, avi")
    return _build_encoded_video_bytes(size_hint_kb, video_format)


def _build_y4m_video_bytes(size_hint_kb: int) -> bytes:
    """生成 Y4M 原始视频内容，作为零依赖视频格式和转码输入。"""
    width = 160
    height = 120
    fps = 12
    bytes_per_frame = width * height * 3
    target_bytes = max(size_hint_kb * 1024, bytes_per_frame)
    frame_count = max(1, target_bytes // (bytes_per_frame + 6))
    output = BytesIO()
    output.write(f"YUV4MPEG2 W{width} H{height} F{fps}:1 Ip A1:1 C444\n".encode("ascii"))

    for frame_index in range(frame_count):
        output.write(b"FRAME\n")
        output.write(_build_y4m_frame(width, height, frame_index))

    return output.getvalue()


def _build_encoded_video_bytes(size_hint_kb: int, video_format: str) -> bytes:
    """调用 ffmpeg 将临时 Y4M 视频转码为目标封装格式。"""
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        raise ValueError(f"生成 {video_format} 视频需要先安装 ffmpeg。")

    source_bytes = _build_y4m_video_bytes(size_hint_kb)
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        source_path = temp_dir_path / "source.y4m"
        target_path = temp_dir_path / f"target.{video_format}"
        source_path.write_bytes(source_bytes)

        command = _build_ffmpeg_command(ffmpeg_path, source_path, target_path, video_format)
        try:
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError as exc:
            raise ValueError(f"ffmpeg 生成 {video_format} 视频失败。") from exc

        return target_path.read_bytes()


def _build_ffmpeg_command(ffmpeg_path: str, source_path: Path, target_path: Path, video_format: str) -> list[str]:
    """根据目标视频格式构造 ffmpeg 转码命令。"""
    command = [ffmpeg_path, "-y", "-i", str(source_path)]

    if video_format == "mp4":
        command.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p"])
    elif video_format == "mkv":
        command.extend(["-c:v", "libx264"])
    elif video_format == "mov":
        command.extend(["-c:v", "mpeg4"])
    elif video_format == "wmv":
        command.extend(["-c:v", "wmv2"])
    elif video_format == "avi":
        command.extend(["-c:v", "mpeg4"])

    command.append(str(target_path))
    return command


def _build_y4m_frame(width: int, height: int, frame_index: int) -> bytes:
    """生成单帧 Y4M 画面数据。"""
    y_plane = bytearray()
    u_plane = bytearray()
    v_plane = bytearray()

    for y in range(height):
        for x in range(width):
            y_plane.append((x + y + frame_index * 7) % 256)
            u_plane.append((64 + frame_index * 13 + x // 2) % 256)
            v_plane.append((128 + frame_index * 17 + y // 2) % 256)

    return bytes(y_plane + u_plane + v_plane)


def _random_hex_color() -> str:
    """生成随机十六进制颜色值。"""
    return f"#{random.randint(0, 0xFFFFFF):06x}"


def _random_rgb_color() -> tuple[int, int, int]:
    """生成随机 RGB 颜色。"""
    return (
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
    )


def _random_rgba_color() -> tuple[int, int, int, int]:
    """生成随机 RGBA 颜色，带半透明通道。"""
    return (
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(64, 220),
    )
