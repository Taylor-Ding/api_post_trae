import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime

from utils.hash_utils import CustNoShardingUtil
from utils.message_parser import MessageParser
from utils.table_query_config import TableQueryConfig, QueryConditionExtractor
from utils.log_manager import LogManager

app = FastAPI(title="数据一致性自动化核对工具API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CheckRequest(BaseModel):
    apiResponse: Optional[Dict[str, Any]] = None
    tables: List[str]
    requestData: Dict[str, Any]
    routingKey: Optional[Dict[str, str]] = None

class CheckResponse(BaseModel):
    success: bool
    logs: List[Dict[str, str]]
    results: List[Dict[str, Any]]
    error: Optional[str] = None

def get_logs():
    """获取日志记录"""
    return []

# 加载数据库配置
def load_db_config():
    config_file = os.path.join(os.path.dirname(__file__), "config", "config.json")
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_db_connection(db_name):
    """获取数据库连接"""
    config = load_db_config()
    db_config = config['databases'][db_name]
    return psycopg2.connect(
        host=db_config['host'],
        port=db_config['port'],
        user=db_config['user'],
        password=db_config['password'],
        database=db_name
    )

def calculate_routing(cust_no_or_medium):
    """根据custNo或mediumNo计算路由"""
    hash_result = CustNoShardingUtil.calculate_hash(cust_no_or_medium)
    db_index = (hash_result - 1) // 2 + 1
    db_name = f"dcdpdb{db_index}"
    table_suffix = f"{hash_result:04d}"
    return db_name, f"tb_dpmst_medium_{table_suffix}", hash_result

def build_where_clause(conditions):
    """根据条件构建WHERE子句"""
    if not conditions:
        return "1=1"
    parts = []
    for field, value in conditions.items():
        parts.append(f"{field} = '{value}'")
    return " AND ".join(parts)

@app.post("/api/check", response_model=CheckResponse)
async def check_data_consistency(request: CheckRequest):
    """
    执行数据一致性检查
    """
    logs = []

    def add_log(message, level="INFO"):
        timestamp = datetime.now().isoformat()
        logs.append({
            "timestamp": timestamp,
            "level": level,
            "message": message
        })

    try:
        add_log("开始执行数据一致性检查...")

        # 1. 解析mainMapElemntInfo字段
        add_log("解析mainMapElemntInfo字段...")
        try:
            routing_info = MessageParser.parse_main_map_element(request.requestData, add_log)
            add_log(f"解析成功: 类型={routing_info['type']}, 值={routing_info['value']}")
        except Exception as e:
            add_log(f"解析mainMapElemntInfo字段失败: {str(e)}", "ERROR")
            raise HTTPException(status_code=400, detail=str(e))

        # 2. 提取各表的查询条件
        add_log("开始提取各表的查询条件...")
        table_conditions = {}
        for table_name in request.tables:
            if not table_name:
                continue
            add_log(f"处理表: {table_name}")
            try:
                conditions = QueryConditionExtractor.extract_conditions(
                    request.requestData,
                    table_name,
                    routing_info,
                    add_log
                )
                table_conditions[table_name] = conditions
            except Exception as e:
                add_log(f"提取表 {table_name} 查询条件失败: {str(e)}", "ERROR")

        # 3. 查询执行前的数据
        add_log("开始查询执行前的数据...")
        before_data = {}
        for table_name, conditions in table_conditions.items():
            if not conditions:
                add_log(f"表 {table_name} 没有查询条件，跳过查询", "WARNING")
                continue

            # 根据条件值计算路由
            condition_value = list(conditions.values())[0]
            db_name, table_name_with_suffix, hash_result = calculate_routing(condition_value)

            add_log(f"路由到: {db_name}.{table_name_with_suffix} (hash={hash_result})")

            # 构建SQL语句
            where_clause = build_where_clause(conditions)
            full_table_name = f"{db_name}.{table_name_with_suffix}"
            sql_query = f'SELECT * FROM "{table_name_with_suffix}" WHERE {where_clause}'
            add_log(f"SQL查询: {sql_query}", "SQL")

            # 执行查询
            try:
                conn = get_db_connection(db_name)
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(sql_query)
                    results = cursor.fetchall()
                    before_data[table_name] = {
                        "sql": sql_query,
                        "count": len(results),
                        "data": [dict(row) for row in results] if results else []
                    }
                    add_log(f"查询到 {len(results)} 条记录")
                conn.close()
            except Exception as e:
                add_log(f"查询失败: {str(e)}", "ERROR")
                before_data[table_name] = {
                    "sql": sql_query,
                    "error": str(e)
                }

        # 4. 调用业务API（如果提供了响应）
        if request.apiResponse:
            add_log("使用提供的API响应进行后续处理...")
        else:
            add_log("未提供API响应，跳过接口调用")

        # 5. 查询执行后的数据
        add_log("开始查询执行后的数据...")
        after_data = {}
        for table_name, conditions in table_conditions.items():
            if not conditions:
                continue

            condition_value = list(conditions.values())[0]
            db_name, table_name_with_suffix, hash_result = calculate_routing(condition_value)

            where_clause = build_where_clause(conditions)
            sql_query = f'SELECT * FROM "{table_name_with_suffix}" WHERE {where_clause}'
            add_log(f"SQL查询: {sql_query}", "SQL")

            try:
                conn = get_db_connection(db_name)
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(sql_query)
                    results = cursor.fetchall()
                    after_data[table_name] = {
                        "sql": sql_query,
                        "count": len(results),
                        "data": [dict(row) for row in results] if results else []
                    }
                    add_log(f"查询到 {len(results)} 条记录")
                conn.close()
            except Exception as e:
                add_log(f"查询失败: {str(e)}", "ERROR")
                after_data[table_name] = {
                    "sql": sql_query,
                    "error": str(e)
                }

        # 6. 比对数据差异
        add_log("开始比对数据差异...")
        results = []
        for table_name in request.tables:
            if not table_name:
                continue

            before = before_data.get(table_name, {})
            after = after_data.get(table_name, {})

            if "error" in before or "error" in after:
                results.append({
                    "table": table_name,
                    "status": "错误",
                    "message": before.get("error") or after.get("error"),
                    "before": before,
                    "after": after,
                    "diff": None
                })
                continue

            # 简单比对
            before_count = before.get("count", 0)
            after_count = after.get("count", 0)

            if before_count == after_count and before.get("data") == after.get("data"):
                results.append({
                    "table": table_name,
                    "status": "通过",
                    "message": "数据一致性检查通过",
                    "before": before,
                    "after": after,
                    "diff": None
                })
            else:
                results.append({
                    "table": table_name,
                    "status": "失败",
                    "message": "数据不一致",
                    "before": before,
                    "after": after,
                    "diff": {"count_changed": True}
                })

        add_log("数据一致性检查完成")

        return CheckResponse(
            success=True,
            logs=logs,
            results=results
        )

    except HTTPException:
        raise
    except Exception as e:
        add_log(f"执行失败: {str(e)}", "ERROR")
        return CheckResponse(
            success=False,
            logs=logs,
            results=[],
            error=str(e)
        )

@app.get("/")
async def root():
    return {"message": "数据一致性自动化核对工具API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)