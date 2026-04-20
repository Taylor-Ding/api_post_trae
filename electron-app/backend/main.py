import os
import sys
from core.db_router import DBRouter
from core.api_caller import APICaller
from core.diff_engine import DiffEngine
from utils.config_manager import ConfigManager
from utils.log_manager import LogManager

class DataConsistencyChecker:
    def __init__(self, config_file):
        # 加载配置
        self.config_manager = ConfigManager(config_file)
        self.config = self.config_manager.config
        
        # 初始化日志
        self.log_manager = LogManager()
        self.logger = self.log_manager.logger
        
        # 初始化各模块
        self.db_router = DBRouter(self.config)
        self.api_caller = APICaller(self.config)
        self.diff_engine = DiffEngine(self.config)
    
    def run(self, cust_no, table_prefix, where_clause, api_url, api_data):
        """
        执行数据一致性检查
        """
        try:
            # 1. 查询接口触发前的数据状态
            self.logger.info(f"开始查询接口触发前的数据状态，custNo: {cust_no}")
            before_data, db_name, table_name = self.db_router.query_data(cust_no, table_prefix, where_clause)
            self.logger.info(f"查询到前数据: {before_data}")
            self.logger.info(f"路由到的库表: {db_name}.{table_name}")
            
            # 2. 调用业务HTTP接口
            self.logger.info(f"开始调用业务接口，URL: {api_url}")
            api_response = self.api_caller.call_api(api_url, data=api_data)
            self.logger.info(f"接口响应: {api_response}")
            
            # 3. 再次查询数据库，获取接口触发后的数据状态
            self.logger.info("开始查询接口触发后的数据状态")
            after_data, _, _ = self.db_router.query_data(cust_no, table_prefix, where_clause)
            self.logger.info(f"查询到后数据: {after_data}")
            
            # 4. 比对前后两次数据库状态的异同
            self.logger.info("开始比对前后数据差异")
            diff = self.diff_engine.compare(before_data, after_data)
            
            if diff:
                self.logger.info(f"数据差异: {diff}")
                return False, diff
            else:
                self.logger.info("数据一致，无差异")
                return True, None
                
        except Exception as e:
            self.logger.error(f"执行过程中发生错误: {str(e)}")
            raise

if __name__ == "__main__":
    # 示例用法
    config_file = os.path.join(os.path.dirname(__file__), "config", "config.json")
    checker = DataConsistencyChecker(config_file)
    
    # 示例参数
    cust_no = "00000194476241"
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
    
    try:
        success, diff = checker.run(cust_no, table_prefix, where_clause, api_url, api_data)
        if success:
            print("数据一致性检查通过")
        else:
            print(f"数据一致性检查失败，差异: {diff}")
    except Exception as e:
        print(f"执行失败: {str(e)}")
        sys.exit(1)