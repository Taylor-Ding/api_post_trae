import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from utils.hash_utils import CustNoShardingUtil

class DBRouter:
    def __init__(self, config):
        self.config = config
    
    def calculate_hash(self, cust_no):
        """
        计算custNo的哈希值
        使用与Java版本相同的哈希算法
        """
        return CustNoShardingUtil.calculate_hash(cust_no)
    
    def get_db_and_table(self, cust_no, table_prefix):
        """
        根据custNo计算路由到的库和表
        """
        hash_result = self.calculate_hash(cust_no)
        db_index = (hash_result - 1) // 2 + 1
        db_name = f"dcdpdb{db_index}"
        table_suffix = f"{hash_result:04d}"
        table_name = f"{table_prefix}_{table_suffix}"
        return db_name, table_name
    
    def query_data(self, cust_no, table_prefix, where_clause):
        """
        执行数据库查询
        """
        db_name, table_name = self.get_db_and_table(cust_no, table_prefix)
        
        # 使用对应数据库的配置
        db_config = self.config['databases'][db_name]
        
        connection = None
        try:
            connection = psycopg2.connect(
                host=db_config['host'],
                port=db_config['port'],
                user=db_config['user'],
                password=db_config['password'],
                database=db_name
            )
            
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                # 使用参数化查询防止SQL注入
                query = sql.SQL("SELECT * FROM {} WHERE {}").format(
                    sql.Identifier(table_name),
                    sql.SQL(where_clause)
                )
                cursor.execute(query)
                result = cursor.fetchall()
                return result, db_name, table_name
        finally:
            if connection:
                connection.close()