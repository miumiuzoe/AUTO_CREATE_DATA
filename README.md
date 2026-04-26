# AUTO_CREATE_DATA

该脚本用于根据协议英文名，从数据库查询协议及其字段信息，自动生成一条测试数据，并输出为 `.bcp` 文件。

当前提供两个独立入口：

- `auto_create_data.py`：生成单个协议数据文件
- `batch_create_data.py`：批量生成协议数据文件

## 功能说明

脚本执行流程如下：

1. 启动后输入协议英文名，支持一次输入多个，多个协议之间用英文逗号 `,` 分隔。
2. 脚本根据输入的 `OBJ_ENGNAME` 查询协议信息。
3. 若只查询到 1 条协议记录，则直接使用该记录的 `OBJ_GUID` 查询字段信息。
4. 若查询到多条协议记录，则先展示候选结果，让用户输入序号选择目标协议，再使用所选协议的 `OBJ_GUID` 查询字段信息。
5. 查询到字段后，按 `IOF_ID` 升序排序，生成一条以 `Tab` 分隔的测试数据。
6. 将结果写入 `.bcp` 文件，输出到 `output` 目录。

## 目录结构

- `app/main.py`：程序入口
- `sql/database.yml`：数据库连接配置
- `sql/fieId.sql`：协议查询 SQL 和字段查询 SQL
- `fakedata/fake.yml`：字段模拟数据规则
- `/output`：生成的 `.bcp` 文件输出目录

## 运行前准备

1. 安装 Python 运行环境。
2. 安装脚本依赖包，至少需要：
   - `sqlalchemy`
   - `pyyaml`
   - 对应数据库驱动：
     - MySQL：`pymysql`
     - PostgreSQL：`pg8000`
     - Oracle：`oracledb`
3. 确保数据库可连接，且相关表、字段存在。
4. 根据实际环境修改数据库配置文件 `sql/database.yml`。

## 数据库配置

在 `sql/database.yml` 中配置：

```yaml
db_type: mysql
host: 127.0.0.1
port: 3306
database: test
username: root
password: 123456
```

说明：

- `db_type` 支持：`mysql`、`postgresql`、`postgres`、`oracle`
- 其余参数按实际数据库填写

## SQL 配置说明

`sql/fieId.sql` 需要包含两段 SQL。

第一段：查询协议候选结果。必须至少返回以下字段：

- `OBJ_GUID`
- `SYS_ID`

建议同时返回一些便于人工识别的字段，例如：

- `OBJ_ENGNAME`
- `OBJ_NAME`
- `OBJ_CHINAME`

第二段：根据选中的协议查询字段信息。当前代码会传入两个参数：

- `:obj_guid`
- `:obj_engname`

字段查询结果至少应包含：

- `IOF_ID`
- `IOF_ENGNAME`

可选返回：

- `IOF_CHINAME`

## 运行方式

在项目根目录执行：

```bash
python3 auto_create_data.py
```

启动后会提示：

```text
请输入协议英文名，多个协议用英文逗号分隔:
```

示例：

```text
ABC_PROTOCOL
```

或

```text
ABC_PROTOCOL,XYZ_PROTOCOL
```

## 批量生成

批量生成使用独立脚本：

```bash
python3 batch_create_data.py
```

启动后会依次提示：

1. 输入协议英文名
2. 选择批量生成方式
3. 输入单文件限制值
4. 输入要生成的文件个数

支持两种方式：

### 按单个文件大小限制

示例：

```text
请输入协议英文名: ABC_PROTOCOL
请选择批量生成方式：
1. 按单个文件大小限制
2. 按单个文件记录条数限制
请输入序号(1/2): 1
请输入单个文件大小限制(MB): 100
请输入要生成的文件个数: 10
```

含义：

- 生成 10 个文件
- 每个文件尽量不超过 `100 MB`
- 若一条记录都放不下，仍会至少写入 1 条记录

批量生成过程中会打印类似信息：

```text
[1/10] 生成成功: output/1001-310000-1714132800-12345-ABC_PROTOCOL-0.bcp，记录数=158234，文件大小=100.00 MB（104857600 字节）
```

### 按单个文件记录条数限制

示例：

```text
请输入协议英文名: ABC_PROTOCOL
请选择批量生成方式：
1. 按单个文件大小限制
2. 按单个文件记录条数限制
请输入序号(1/2): 2
请输入单个文件记录条数限制: 1000
请输入要生成的文件个数: 10
```

含义：

- 生成 10 个文件
- 每个文件写入 1000 条记录

## 交互逻辑

### 查询到单条协议

如果某个协议英文名只查到一条记录，则脚本直接继续查询字段并生成文件，不需要额外选择。

### 查询到多条协议

如果某个协议英文名查到多条记录，脚本会打印候选协议列表，例如：

```text
协议 ABC_PROTOCOL 查询到多个结果，请选择要生成数据的目标协议：
1. OBJ_GUID=xxx, SYS_ID=1001, OBJ_ENGNAME=ABC_PROTOCOL
2. OBJ_GUID=yyy, SYS_ID=1002, OBJ_ENGNAME=ABC_PROTOCOL
请输入序号:
```

输入对应序号后，脚本会使用该条记录的 `OBJ_GUID` 查询字段信息。

## 生成规则

字段数据生成规则如下：

1. 字段顺序按 `IOF_ID` 升序排列。
2. 若字段未命中 `fakedata/fake.yml` 中的规则，则默认生成空字符串。
3. 所有字段使用 `Tab` 分隔，组成一条完整记录。
4. 若 `fakedata/fake.yml` 中为某些字段配置了特殊规则，则优先按配置生成。

## 输出结果

生成成功后，脚本会在 `output` 目录下输出 `.bcp` 文件，并打印类似信息：

```text
ABC_PROTOCOL 生成成功: /Users/zxw/vscodeworkspace/demo/AUTO_CREATE_DATA/output/xxx.bcp
```

文件名格式为：

```text
{sys}-310000-{10位当前时间戳}-{随机五位数}-{OBJ_ENGNAME}-0.bcp
```

其中：

- `{sys}`：取自协议查询结果中的 `SYS_ID`
- `{OBJ_ENGNAME}`：为输入的协议英文名

## 注意事项

1. 协议英文名输入后，代码本身不会自动转大写或小写。
2. 是否大小写敏感，取决于数据库及字段比较规则。
3. 若协议查询结果缺少 `OBJ_GUID` 或 `SYS_ID`，脚本会直接报错。
4. 若字段查询结果为空，脚本会报错，提示未找到对应字段信息。
5. `sql/fieId.sql` 中必须是两段真实可执行 SQL。
6. 批量生成脚本一次只处理一个协议英文名。
7. 按大小生成时，文件大小按 UTF-8 编码后的实际字节数计算，单位输入为 `MB`。

## 常见报错说明

`未找到协议: xxx`

说明按输入的 `OBJ_ENGNAME` 没查到协议信息。

`协议查询结果中缺少 OBJ_GUID 字段`

说明第一段 SQL 没有返回 `OBJ_GUID`。

`协议查询结果中缺少 SYS_ID 字段`

说明第一段 SQL 没有返回 `SYS_ID`。

`未找到 OBJ_GUID=xxx 对应的协议字段`

说明第二段 SQL 没有查到该协议对应的字段信息。

`sqlalchemy.exc.ResourceClosedError`

通常说明 SQL 文件解析异常，或执行的不是返回结果集的查询语句。
