import logging
import os
from datetime import datetime

class LogManager:
    def __init__(self, log_dir='logs', log_file='sync_test.log'):
        self.log_dir = log_dir
        self.log_file = log_file
        self.logger = self.setup_logger()
    
    def setup_logger(self):
        """
        设置日志配置
        """
        # 确保日志目录存在
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        # 创建logger
        logger = logging.getLogger('data_consistency_checker')
        logger.setLevel(logging.INFO)
        
        # 避免重复添加handler
        if not logger.handlers:
            # 创建控制台handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # 创建文件handler
            file_handler = logging.FileHandler(
                os.path.join(self.log_dir, self.log_file),
                encoding='utf-8'
            )
            file_handler.setLevel(logging.INFO)
            
            # 设置日志格式
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
            file_handler.setFormatter(formatter)
            
            # 添加handler
            logger.addHandler(console_handler)
            logger.addHandler(file_handler)
        
        return logger
    
    def info(self, message):
        """
        记录info级别日志
        """
        self.logger.info(message)
    
    def error(self, message):
        """
        记录error级别日志
        """
        self.logger.error(message)
    
    def debug(self, message):
        """
        记录debug级别日志
        """
        self.logger.debug(message)