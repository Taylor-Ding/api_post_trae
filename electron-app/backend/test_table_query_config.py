import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.table_query_config import TableQueryConfig, QueryConditionExtractor

def test_table_query_config():
    """
    测试表查询条件配置和提取功能
    """
    print("=== 测试表查询条件配置 ===\n")

    # 测试数据
    request_data = {
        "txBody": {
            "txEntity": {
                "inputModeCode": "2",
                "coreTxFlag": "00000000000000",
                "mediumNo": "6217991000103398751"
            },
            "txComni": {
                "accountingDate": "20231026"
            },
            "txComn7": {
                "custNo": "00400022300118",
                "teschnlCustNo": "4067745905991"
            },
            "txComn8": {
                "busiSendSysOrCmptNo": "99100060000"
            }
        },
        "txHeader": {
            "mainMapElemntInfo": "056217991000103398751"
        }
    }

    test_cases = [
        {
            "name": "测试05开头路由键(mediumNo) -> tb_dpmst_medium",
            "routing_key": {"type": "medium_no", "value": "6217991000103398751"},
            "table": "tb_dpmst_medium",
            "expected": {"medium_no": "6217991000103398751"}
        },
        {
            "name": "测试从报文中直接提取条件",
            "routing_key": None,
            "table": "tb_dpmst_medium",
            "expected": {"medium_no": "6217991000103398751"}
        }
    ]

    passed = 0
    failed = 0

    for test_case in test_cases:
        print(f"测试: {test_case['name']}")
        try:
            conditions = QueryConditionExtractor.extract_conditions(
                request_data,
                test_case['table'],
                test_case['routing_key']
            )
            expected = test_case['expected']

            if conditions == expected:
                print(f"  ✅ 通过: {conditions}")
                passed += 1
            else:
                print(f"  ❌ 失败: 期望 {expected}, 实际 {conditions}")
                failed += 1
        except Exception as e:
            print(f"  ❌ 失败: 异常 - {str(e)}")
            failed += 1
        print()

    # 测试配置获取
    print("=== 测试配置获取 ===\n")
    tables = TableQueryConfig.get_all_tables()
    print(f"已配置的表: {tables}")

    config = TableQueryConfig.get_table_config("tb_dpmst_medium")
    print(f"tb_dpmst_medium 配置: {config}")

    print(f"\n=== 测试结果: {passed} 通过, {failed} 失败 ===")

if __name__ == "__main__":
    test_table_query_config()