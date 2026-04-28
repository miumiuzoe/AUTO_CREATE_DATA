# AUTO_CREATE_DATA

根据协议英文名从数据库查询协议和字段信息，按配置规则生成测试数据。项目当前提供两个独立入口：

- `auto_create_data.py`：生成普通 `.bcp` 文件
- `zip_create_data.py`：生成只包含 `.bcp` 和模板 XML 的 `.zip` 压缩包

两个入口都支持一次输入多个协议英文名，多个协议之间用英文逗号 `,` 分隔。

## 目录结构

```text
AUTO_CREATE_DATA/
├─ auto_create_data.py          # 普通 BCP 生成入口
├─ zip_create_data.py           # ZIP 包生成入口
├─ common/                      # 公共能力：数据库、配置读取、协议选择、假数据、文件命名
├─ features/
│  ├─ bcp/                      # 普通 BCP 功能模块
│  └─ zip_package/              # ZIP 包功能模块
├─ config/
│  ├─ database.yml              # 数据库连接配置
│  └─ fake.yml                  # 字段模拟数据规则
├─ sql/
│  └─ fieId.sql                 # 协议查询 SQL 和字段查询 SQL
├─ template/
│  └─ zip.xml                   # ZIP 包中的 XML 模板
└─ output/                      # 输出目录
```

## 运行前准备

安装依赖：

```bash
pip install sqlalchemy pyyaml faker pymysql
```

如果使用其他数据库，需要安装对应驱动：

- PostgreSQL：`pg8000`
- Oracle：`oracledb`

## 配置

数据库配置在 `config/database.yml`：

```yaml
db_type: mysql
host: 127.0.0.1
port: 3306
database: test
username: root
password: 123456
```

假数据规则在 `config/fake.yml`。规则 key 格式为：

```yaml
字段英文名[字段中文关键字]: 生成规则
```

示例：

```yaml
NAME[姓名]: faker.name()
TIME[时间]: date_methods.now_timestamp_ms()
CITY[城市]: SELECT city_code FROM bscdata.city
```

英文名使用精确匹配，中文名使用包含匹配。未命中规则的字段默认生成空字符串。

## SQL 文件

`sql/fieId.sql` 需要包含两段可执行查询 SQL，以分号分隔。

第一段用于查询协议候选结果，至少返回：

- `OBJ_GUID`
- `SYS_ID`

第二段用于查询协议字段信息，当前会传入：

- `:obj_guid`
- `:obj_engname`

字段查询结果至少返回：

- `IOF_ID`
- `IOF_ENGNAME`

ZIP 功能还会使用：

- `IOF_KEYNAME`
- `IOF_CHINAME`

## 普通生成 BCP

```bash
python auto_create_data.py
```

输入示例：

```text
ABC_PROTOCOL,XYZ_PROTOCOL
```

每个协议会在 `output` 下生成一个 `.bcp` 文件。文件名格式：

```text
{sys_id}-310000-{10位时间戳}-{随机五位数}-{协议英文名}-0.bcp
```

## 生成 ZIP 包

```bash
python zip_create_data.py
```

输入一个或多个协议英文名后，每个协议会生成一个 `.zip` 文件。ZIP 文件名格式：

```text
{sys_id}-330000-330000-{10位时间戳}-{随机五位数}.zip
```

ZIP 包内只包含两个文件：

- 生成的 `.bcp` 文件
- `zip.xml`

`zip.xml` 使用 `template/zip.xml` 作为模板，并按以下规则修改：

- `ITEM key="01A0004"` 的 `val` 改为协议英文名
- `ITEM key="01A0005"` 的 `val` 改为协议 `sys_id`
- `ITEM key="01A0006"` 的 `val` 改为 BCP 文件名
- `DATASET name="COMMON_0015"` 下的 `DATA` 写入协议字段列表

字段列表格式：

```xml
<ITEM key="IOF_KEYNAME" eng="IOF_ENGNAME" chn="IOF_CHINAME" />
```

XML 生成使用节点和属性查找，不依赖模板固定行号；模板结构可以调整，但需要保留上述 key 和 `COMMON_0015` 数据集。

## 多协议选择逻辑

每个协议英文名都会先查询候选协议：

- 如果只查到一条协议记录，脚本直接使用该协议。
- 如果查到多条协议记录，脚本会打印候选列表，并要求输入序号选择。

## 常见报错

`未找到协议: xxx`

说明按输入的 `OBJ_ENGNAME` 没查到协议信息。

`协议查询结果中缺少 OBJ_GUID 字段`

说明第一段 SQL 没有返回 `OBJ_GUID`。

`协议查询结果中缺少 SYS_ID 字段`

说明第一段 SQL 没有返回 `SYS_ID`。

`未找到 OBJ_GUID=xxx 对应的协议字段`

说明第二段 SQL 没有查到对应字段信息。

`Access denied for user ...`

说明已经连到数据库，但账号密码或 MySQL 用户 host 授权不正确。建议使用单独的只读账号，不要直接使用远程 root。
