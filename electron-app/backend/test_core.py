import os
import sys
import unittest
from unittest.mock import Mock, patch

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.db_router import DBRouter
from core.api_caller import APICaller
from core.diff_engine import DiffEngine
from utils.config_manager import ConfigManager
from utils.log_manager import LogManager

class TestCoreModules(unittest.TestCase):
    def setUp(self):
        # 测试配置
        self.test_config = {
            "databases": {
                "dcdpdb1": {
                    "host": "localhost",
                    "port": 3306,
                    "user": "root",
                    "password": "password"
                }
            },
            "api_timeout": 30,
            "ignore_fields": [
                "update_time",
                "version",
                "trace_id",
                "create_time"
            ]
        }
    
    def test_config_manager(self):
        """测试配置管理模块"""
        # 创建临时配置文件
        import tempfile
        import json
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.test_config, f)
            temp_config_file = f.name
        
        try:
            # 测试配置加载
            config_manager = ConfigManager(temp_config_file)
            self.assertEqual(config_manager.get('api_timeout'), 30)
            self.assertEqual(config_manager.get('databases.dcdpdb1.host'), 'localhost')
            self.assertEqual(config_manager.get('non_existent_key', 'default'), 'default')
        finally:
            # 清理临时文件
            os.unlink(temp_config_file)
    
    def test_db_router(self):
        """测试数据库路由模块"""
        db_router = DBRouter(self.test_config)
        
        # 测试哈希计算
        hash_result = db_router.calculate_hash('123456')
        self.assertGreaterEqual(hash_result, 1)
        self.assertLessEqual(hash_result, 8)
        
        # 测试库表路由
        db_name, table_name = db_router.get_db_and_table('123456', 'tb_dpmst_medium')
        self.assertIn(db_name, ['dcdpdb1', 'dcdpdb2', 'dcdpdb3', 'dcdpdb4'])
        self.assertTrue(table_name.startswith('tb_dpmst_medium_'))
    
    @patch('core.api_caller.requests.post')
    def test_api_caller(self, mock_post):
        """测试接口调用模块"""
        # 模拟API响应
        mock_response = Mock()
        mock_response.json.return_value = {"status": "success", "data": {"id": 1}}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        api_caller = APICaller(self.test_config)
        
        # 测试API调用
        api_url = "http://localhost:8080/api/business"
        api_data = {"custNo": "123456", "action": "update", "data": {"name": "测试用户", "address": None}}
        
        response = api_caller.call_api(api_url, data=api_data)
        self.assertEqual(response, {"status": "success", "data": {"id": 1}})
        
        # 验证请求参数
        mock_post.assert_called_once_with(
            api_url,
            headers={"Content-Type": "application/json"},
            json=api_data,
            timeout=30
        )
    
    def test_diff_engine(self):
        """测试数据比对模块"""
        diff_engine = DiffEngine(self.test_config)
        
        # 测试数据比对
        before_data = [
            {"id": 1, "name": "测试用户", "age": 30, "update_time": "2023-01-01 00:00:00"}
        ]
        after_data = [
            {"id": 1, "name": "测试用户", "age": 31, "update_time": "2023-01-02 00:00:00"}
        ]
        
        diff = diff_engine.compare(before_data, after_data)
        # 应该检测到age字段的变化，而忽略update_time字段
        self.assertIn('values_changed', diff)
        
        # 测试无差异情况
        before_data2 = [
            {"id": 1, "name": "测试用户", "age": 30, "update_time": "2023-01-01 00:00:00"}
        ]
        after_data2 = [
            {"id": 1, "name": "测试用户", "age": 30, "update_time": "2023-01-02 00:00:00"}
        ]
        
        diff2 = diff_engine.compare(before_data2, after_data2)
        self.assertEqual(len(diff2), 0)

if __name__ == '__main__':
    unittest.main()