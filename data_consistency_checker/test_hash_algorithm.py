import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.hash_utils import HashUtils, CustNoShardingUtil

def test_hash_algorithm():
    """
    测试哈希算法的正确性
    """
    print("=== 哈希算法测试 ===\n")
    
    # 测试数据
    test_cust_nos = [
        "100001",
        "100002",
        "100003",
        "100004",
        "100005",
        "100006",
        "100007",
        "100008",
        "123456",
        "987654"
    ]
    
    print("测试HashUtils.hash32:")
    print("-" * 60)
    for cust_no in test_cust_nos:
        hash_value = HashUtils.hash32(cust_no)
        print(f"custNo: {cust_no:6} → hash32: {hash_value:11}")
    
    print("\n测试CustNoShardingUtil:")
    print("-" * 60)
    for cust_no in test_cust_nos:
        sharding_id = CustNoShardingUtil.determine_sharding_id_by_cust_no(cust_no, 8)
        hash_result = CustNoShardingUtil.calculate_hash(cust_no)
        print(f"custNo: {cust_no:6} → sharding_id: {sharding_id:4} → hash_result: {hash_result:2}")
    
    print("\n测试DBRouter路由:")
    print("-" * 60)
    from core.db_router import DBRouter
    import json
    
    # 加载配置
    config_file = os.path.join(os.path.dirname(__file__), "config", "config.json")
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    db_router = DBRouter(config)
    
    for cust_no in test_cust_nos:
        hash_result = db_router.calculate_hash(cust_no)
        db_name, table_name = db_router.get_db_and_table(cust_no, "tb_dpmst_medium")
        print(f"custNo: {cust_no:6} → hash: {hash_result:2} → {db_name}.{table_name}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_hash_algorithm()