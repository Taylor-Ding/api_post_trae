# 数据一致性自动化核对工具

## 项目简介

这是一个用于分布式系统"查-发-查-比"的数据一致性自动化核对工具，主要用于验证业务接口执行前后的数据一致性。

## 核心功能

1. **数据库路由与查询**：根据用户标识（`custNo`）路由到指定的分库分表，执行动态查询。
2. **接口调用**：调用业务HTTP接口，确保空值在JSON序列化时被完整保留。
3. **数据比对**：比对接口执行前后的数据库状态，验证接口逻辑的正确性。
4. **噪音排除**：支持使用正则表达式排除不需要比对的动态字段。

## 项目结构

```
data_consistency_checker/
├── config/            # 配置文件目录
│   └── config.json    # 配置文件
├── core/              # 核心模块
│   ├── db_router.py   # 数据库路由与查询模块
│   ├── api_caller.py  # 接口调用模块
│   └── diff_engine.py # 数据比对模块
├── utils/             # 工具模块
│   ├── config_manager.py # 配置管理模块
│   └── log_manager.py    # 日志管理模块
├── logs/              # 日志目录
├── main.py            # 主执行脚本
├── requirements.txt   # 依赖文件
├── run.sh             # 启动脚本
└── README.md          # 说明文档
```

## 部署与执行指南

### 环境要求

- Python 3.6+
- pip 3+
- Linux 操作系统

### 部署步骤

1. **克隆项目**：将项目代码克隆到Linux服务器上。

2. **配置修改**：编辑 `config/config.json` 文件，修改数据库连接信息和其他配置：

   ```json
   {
     "databases": {
       "dcdpdb1": {
         "host": "数据库主机地址",
         "port": 3306,
         "user": "数据库用户名",
         "password": "数据库密码"
       },
       // 其他数据库配置...
     },
     "api_timeout": 30,
     "ignore_fields": [
       "update_time",
       "version",
       "trace_id",
       "create_time"
     ]
   }
   ```

3. **执行启动脚本**：在项目根目录下执行 `run.sh` 脚本：

   ```bash
   ./run.sh
   ```

   该脚本会自动安装依赖并执行数据一致性检查。

### 执行流程

1. **查询接口触发前的数据状态**：根据 `custNo` 路由到指定的分库分表，执行查询。
2. **调用业务HTTP接口**：发送JSON报文，触发业务逻辑。
3. **查询接口触发后的数据状态**：再次执行查询，获取最新数据。
4. **比对前后数据差异**：使用 `deepdiff` 库比对前后数据的异同，排除动态字段的影响。
5. **输出结果**：在控制台和日志文件中输出执行结果。

### 日志查看

日志文件存储在 `logs/sync_test.log` 中，可以使用以下命令查看：

```bash
tail -f logs/sync_test.log
```

### 自定义执行

可以修改 `main.py` 文件中的示例参数，根据实际业务场景执行数据一致性检查：

```python
# 示例参数
cust_no = "123456"
table_prefix = "tb_dpmst_medium"
where_clause = f"cust_no = '{cust_no}'"
api_url = "http://localhost:8080/api/business"
api_data = {
    "custNo": cust_no,
    "action": "update",
    "data": {
        "name": "测试用户",
        "age": 30,
        "address": None  # 测试空值保留
    }
}
```

## 注意事项

1. **数据库连接**：确保配置文件中的数据库连接信息正确，并且服务器可以访问数据库。
2. **接口地址**：确保 `api_url` 指向正确的业务接口地址。
3. **路由算法**：如需使用自定义的路由算法，请修改 `db_router.py` 文件中的 `calculate_hash` 方法。
4. **忽略字段**：如需添加或修改需要忽略的字段，请修改 `config.json` 文件中的 `ignore_fields` 列表。

## 依赖说明

- `pymysql`：用于数据库连接和查询。
- `requests`：用于发送HTTP请求。
- `deepdiff`：用于比对数据差异。