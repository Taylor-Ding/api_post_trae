import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.db_router import DBRouter

def test_db_router():
    """
    测试数据库路由和查询功能
    """
    # 加载配置文件
    config_file = os.path.join(os.path.dirname(__file__), "config", "config.json")
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 初始化数据库路由器
    db_router = DBRouter(config)
    
    print("=== 数据库路由和查询测试 ===\n")
    
    # 测试不同的custNo，验证路由是否正确
    test_cases = [
        ("100001", "tb_dpmst_medium"),
        ("100002", "tb_dpmst_medium"),
        ("100003", "tb_dpmst_medium"),
        ("100004", "tb_dpmst_medium"),
        ("100005", "tb_dpmst_medium"),
        ("100006", "tb_dpmst_medium"),
        ("100007", "tb_dpmst_medium"),
        ("100008", "tb_dpmst_medium"),
    ]
    
    all_tests_passed = True
    
    for cust_no, table_prefix in test_cases:
        print(f"测试 custNo: {cust_no}")
        
        try:
            # 计算路由
            db_name, table_name = db_router.get_db_and_table(cust_no, table_prefix)
            print(f"  路由结果: {db_name}.{table_name}")
            
            # 验证路由是否正确
            hash_result = db_router.calculate_hash(cust_no)
            expected_db_index = (hash_result - 1) // 2 + 1
            expected_db_name = f"dcdpdb{expected_db_index}"
            expected_table_suffix = f"{hash_result:04d}"
            expected_table_name = f"{table_prefix}_{expected_table_suffix}"
            
            if db_name == expected_db_name and table_name == expected_table_name:
                print(f"  ✓ 路由计算正确")
            else:
                print(f"  ✗ 路由计算错误，期望: {expected_db_name}.{expected_table_name}")
                all_tests_passed = False
            
            # 执行查询
            where_clause = "1=1 LIMIT 1"  # 只查询一条记录进行测试
            result, actual_db_name, actual_table_name = db_router.query_data(cust_no, table_prefix, where_clause)
            
            if result:
                print(f"  ✓ 查询成功，返回 {len(result)} 条记录")
                print(f"  ✓ 实际访问的库表: {actual_db_name}.{actual_table_name}")
                
                # 显示第一条记录的部分字段
                if result and len(result) > 0:
                    first_record = result[0]
                    print(f"  ✓ 第一条记录字段数: {len(first_record)}")
                    # 显示前5个字段
                    field_names = list(first_record.keys())[:5]
                    print(f"  ✓ 字段示例: {', '.join(field_names)}")
            else:
                print(f"  ✗ 查询失败或无数据")
                all_tests_passed = False
                
        except Exception as e:
            print(f"  ✗ 执行查询时出错: {str(e)}")
            all_tests_passed = False
        
        print()
    
    print("=== 测试结果 ===")
    if all_tests_passed:
        print("✓ 所有数据库路由和查询测试通过")
        return True
    else:
        print("✗ 部分数据库路由和查询测试失败")
        return False

if __name__ == "__main__":
    success = test_db_router()
    sys.exit(0 if success else 1)