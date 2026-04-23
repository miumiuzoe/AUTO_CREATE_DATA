# AUTO CREATE DATA
## 该脚本旨在自动生成合规的指定协议的则试数据，并输出到。bcp文件，包含的功能如下：
1. 脚本启动时提示输入协议英文名，根据输入的内容，连接数据库(连接信息在sql/database.yml可配)查询协议信息(查询sql在sql/fieId.sql，使用参数 `:obj_engname` 传入协议英文名)，需支持oracle,mysql,PostgreSQL数据库
2.	根据查询出的字段信息(查询结果示例在sql/example.txt)，组成一条以tab键分隔的测试数据，字段内容默认为(IOF_ID)_(IOF_ENGNAME)，字段顺序以IOFID递增排序
*例如：1 CLUE ID 2 CLUE SRC SYS.3 CLUE DST SYS*
3. 个性化修改测试数据，使数据更为真实，具体办法如下：
    读取IOF_ENGNAME和IOF_CHINAME，与配置文件fakedata/fake.yml比对，IOF_ENGNAME包含MSISDN或IOF_CHINAME包含电话，则调用fk.phonenumber()生成测试数据，以此类推，没匹配到则用默认的字段内容;
    若字段后面不是faker方法，则随意选取列表中的内容
4. 测试数据构造完成后，根据示例的文件名格式，生成.bcp文件，将测试数据写入

** 测试文件名示例：{sys}-310000-{10位当前时间戳}-(随机五位数)-(OBJ_ENGNAME}-0.bCp **
{sys}取值为sql/fieId.sql中的查询协议的SYS_ID
{OBJ_ENGNAME}就是用户输入的协议英文名
