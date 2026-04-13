import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import psycopg2
import json

def check_table_data():
    """
    检查tb_dpmst_medium_0002表中的数据
    """
    # 加载配置
    config_file = os.path.join(os.path.dirname(__file__), "config", "config.json")
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 连接数据库
    db_config = config['databases']['dcdpdb1']
    connection = None
    
    try:
        connection = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            database='dcdpdb1'
        )
        
        print("=== 检查表结构 ===")
        # 检查表结构
        with connection.cursor() as cursor:
            # 查询表结构
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'tb_dpmst_medium_0002' 
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            print(f"表 tb_dpmst_medium_0002 共有 {len(columns)} 个字段:")
            for col in columns:
                print(f"  - {col[0]} ({col[1]})")
        
        print("\n=== 检查所有记录 ===")
        # 检查所有记录
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM tb_dpmst_medium_0002 LIMIT 10")
            records = cursor.fetchall()
            print(f"表 tb_dpmst_medium_0002 共有 {len(records)} 条记录 (最多显示10条):")
            for i, record in enumerate(records):
                print(f"\n记录 {i+1}:")
                # 打印每个字段的值
                for j, col in enumerate(columns):
                    print(f"  {col[0]}: {record[j]}")
        
        print("\n=== 检查特定客户号 ===")
        # 检查特定客户号
        with connection.cursor() as cursor:
            cust_no = "00000194476241"
            cursor.execute("SELECT * FROM tb_dpmst_medium_0002 WHERE cust_no = %s", (cust_no,))
            record = cursor.fetchone()
            if record:
                print(f"找到客户 {cust_no} 的记录:")
                for j, col in enumerate(columns):
                    print(f"  {col[0]}: {record[j]}")
            else:
                print(f"未找到客户 {cust_no} 的记录")
                
            # 检查是否有类似的客户号
            cursor.execute("SELECT cust_no FROM tb_dpmst_medium_0002")
            all_cust_nos = cursor.fetchall()
            print(f"\n表中所有客户号:")
            for cust in all_cust_nos:
                print(f"  - {cust[0]}")
                
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    check_table_data()