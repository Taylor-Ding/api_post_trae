import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.hash_utils import HashUtils, CustNoShardingUtil

def debug_hash(cust_no):
    """
    详细调试哈希算法
    """
    print(f"=== 调试客户号: {cust_no} ===")
    
    # 计算哈希值
    hash_value = HashUtils.hash32(cust_no)
    print(f"1. 原始哈希值: {hash_value}")
    
    # 处理负数
    if hash_value < 0:
        hash_value = -hash_value
    print(f"2. 取绝对值后: {hash_value}")
    
    # 计算分片编号
    total_sharding = 8
    sharding_number = (hash_value % total_sharding) + 1
    print(f"3. 分片编号: {sharding_number}")
    
    # 计算库索引
    db_index = (sharding_number - 1) // 2 + 1
    print(f"4. 库索引: {db_index}")
    
    # 计算表后缀
    table_suffix = f"{sharding_number:04d}"
    print(f"5. 表后缀: {table_suffix}")
    
    # 计算最终路由
    db_name = f"dcdpdb{db_index}"
    table_name = f"tb_dpmst_medium_{table_suffix}"
    print(f"6. 最终路由: {db_name}.{table_name}")
    
    # 验证CustNoShardingUtil的结果
    sharding_id = CustNoShardingUtil.determine_sharding_id_by_cust_no(cust_no, total_sharding)
    print(f"7. CustNoShardingUtil分片ID: {sharding_id}")
    
    return sharding_number, db_name, table_name

if __name__ == "__main__":
    # 测试客户号
    cust_no = "00000194476241"
    debug_hash(cust_no)
    
    # 测试其他客户号作为参考
    print("\n=== 参考测试 ===")
    test_cust_nos = ["00001129443560"]
    for test_cust in test_cust_nos:
        print(f"\n客户号: {test_cust}")
        sharding_number, db_name, table_name = debug_hash(test_cust)
        print(f"路由结果: {db_name}.{table_name}")