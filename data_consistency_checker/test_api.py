import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
import json

def test_api():
    """测试API服务"""
    url = "http://localhost:8080/api/check"

    request_data = {
        "apiResponse": None,
        "tables": ["tb_dpmst_medium"],
        "requestData": {
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
        },
        "routingKey": None
    }

    try:
        print("发送请求到API...")
        response = requests.post(url, json=request_data, timeout=30)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except requests.exceptions.ConnectionError as e:
        print(f"连接错误: {e}")
        print("请确保API服务正在运行: python api_server.py")
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    test_api()