import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.hash_utils import CustNoShardingUtil
from core.db_router import DBRouter
import json

def calculate_route(cust_no):
    """
    计算客户号的路由库表
    """
    # 加载配置
    config_file = os.path.join(os.path.dirname(__file__), "config", "config.json")
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 初始化DBRouter
    db_router = DBRouter(config)
    
    # 计算哈希值
    hash_result = db_router.calculate_hash(cust_no)
    
    # 计算路由到的库和表
    db_name, table_name = db_router.get_db_and_table(cust_no, "tb_dpmst_medium")
    
    # 输出结果
    print(f"客户号: {cust_no}")
    print(f"哈希值: {hash_result}")
    print(f"路由到: {db_name}.{table_name}")
    
    return db_name, table_name

if __name__ == "__main__":
    # 测试客户号
    cust_no = "00000194476241"
    calculate_route(cust_no)