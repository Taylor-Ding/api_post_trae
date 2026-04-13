import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    print("错误: 未安装psycopg2库，正在安装...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"])
    import psycopg2
    from psycopg2 import sql

def test_database_connection():
    """
    测试数据库连接和表访问
    """
    # 加载配置文件
    config_file = os.path.join(os.path.dirname(__file__), "config", "config.json")
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 定义数据库和表的映射关系
    db_table_mapping = {
        "dcdpdb1": ["tb_dpmst_medium_0001", "tb_dpmst_medium_0002"],
        "dcdpdb2": ["tb_dpmst_medium_0003", "tb_dpmst_medium_0004"],
        "dcdpdb3": ["tb_dpmst_medium_0005", "tb_dpmst_medium_0006"],
        "dcdpdb4": ["tb_dpmst_medium_0007", "tb_dpmst_medium_0008"]
    }
    
    print("=== 数据库连接测试 ===\n")
    
    all_tests_passed = True
    
    # 测试每个数据库
    for db_name, tables in db_table_mapping.items():
        print(f"正在测试数据库: {db_name}")
        db_config = config['databases'][db_name]
        
        try:
            # 连接数据库
            connection = psycopg2.connect(
                host=db_config['host'],
                port=db_config['port'],
                user=db_config['user'],
                password=db_config['password'],
                database=db_name
            )
            
            print(f"  ✓ 成功连接到数据库 {db_name}")
            
            # 测试每个表
            cursor = connection.cursor()
            for table_name in tables:
                try:
                    # 检查表是否存在
                    check_table_query = sql.SQL("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = %s
                        )
                    """)
                    cursor.execute(check_table_query, (table_name,))
                    result = cursor.fetchone()
                    table_exists = result[0] if result else False
                    
                    if table_exists:
                        # 查询表中的记录数
                        count_query = sql.SQL("SELECT COUNT(*) FROM {}").format(
                            sql.Identifier(table_name)
                        )
                        cursor.execute(count_query)
                        result = cursor.fetchone()
                        record_count = result[0] if result else 0
                        
                        # 查询表结构
                        structure_query = sql.SQL("""
                            SELECT column_name, data_type 
                            FROM information_schema.columns 
                            WHERE table_name = %s 
                            ORDER BY ordinal_position
                        """)
                        cursor.execute(structure_query, (table_name,))
                        columns = cursor.fetchall()
                        
                        print(f"    ✓ 表 {table_name} 存在")
                        print(f"      记录数: {record_count}")
                        print(f"      字段数: {len(columns)}")
                        if columns:
                            print(f"      字段列表: {', '.join([col[0] for col in columns[:5]])}{'...' if len(columns) > 5 else ''}")
                    else:
                        print(f"    ✗ 表 {table_name} 不存在")
                        all_tests_passed = False
                        
                except Exception as e:
                    print(f"    ✗ 访问表 {table_name} 时出错: {str(e)}")
                    all_tests_passed = False
            
            cursor.close()
            connection.close()
            print()
            
        except Exception as e:
            print(f"  ✗ 连接数据库 {db_name} 失败: {str(e)}")
            all_tests_passed = False
            print()
    
    print("=== 测试结果 ===")
    if all_tests_passed:
        print("✓ 所有数据库连接测试通过")
        return True
    else:
        print("✗ 部分数据库连接测试失败")
        return False

if __name__ == "__main__":
    success = test_database_connection()
    sys.exit(0 if success else 1)