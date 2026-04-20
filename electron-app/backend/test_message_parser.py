import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.message_parser import MessageParser

def test_parser():
    """
    测试消息解析功能
    """
    print("=== 测试消息解析功能 ===\n")

    test_cases = [
        {
            "name": "测试04开头客户号",
            "data": {
                "txHeader": {
                    "mainMapElemntInfo": "0400400022300118"
                }
            },
            "expected_type": "cust_no",
            "expected_value": "00400022300118"
        },
        {
            "name": "测试05开头介质号",
            "data": {
                "txHeader": {
                    "mainMapElemntInfo": "056217991000103398751"
                }
            },
            "expected_type": "medium_no",
            "expected_value": "6217991000103398751"
        },
        {
            "name": "测试null值",
            "data": {
                "txHeader": {
                    "mainMapElemntInfo": None
                }
            },
            "should_raise": True
        },
        {
            "name": "测试空字符串",
            "data": {
                "txHeader": {
                    "mainMapElemntInfo": ""
                }
            },
            "should_raise": True
        },
        {
            "name": "测试04开头但无客户号",
            "data": {
                "txHeader": {
                    "mainMapElemntInfo": "04"
                }
            },
            "should_raise": True
        },
        {
            "name": "测试05开头但无介质号",
            "data": {
                "txHeader": {
                    "mainMapElemntInfo": "05"
                }
            },
            "should_raise": True
        },
        {
            "name": "测试无效前缀",
            "data": {
                "txHeader": {
                    "mainMapElemntInfo": "0640400022300118"
                }
            },
            "should_raise": True
        },
        {
            "name": "测试缺少txHeader",
            "data": {},
            "should_raise": True
        },
        {
            "name": "测试缺少mainMapElemntInfo字段",
            "data": {
                "txHeader": {}
            },
            "should_raise": True
        }
    ]

    passed = 0
    failed = 0

    for test_case in test_cases:
        print(f"测试: {test_case['name']}")
        try:
            result = MessageParser.parse_main_map_element(test_case['data'])
            if test_case.get('should_raise'):
                print(f"  ❌ 失败: 预期抛出异常但没有抛出")
                failed += 1
            else:
                if result['type'] == test_case['expected_type'] and result['value'] == test_case['expected_value']:
                    print(f"  ✅ 通过: type={result['type']}, value={result['value']}")
                    passed += 1
                else:
                    print(f"  ❌ 失败: 期望 type={test_case['expected_type']}, value={test_case['expected_value']}, 实际 type={result['type']}, value={result['value']}")
                    failed += 1
        except Exception as e:
            if test_case.get('should_raise'):
                print(f"  ✅ 通过: 正确抛出异常 - {str(e)}")
                passed += 1
            else:
                print(f"  ❌ 失败: 意外抛出异常 - {str(e)}")
                failed += 1
        print()

    print(f"=== 测试结果: {passed} 通过, {failed} 失败 ===")

if __name__ == "__main__":
    test_parser()