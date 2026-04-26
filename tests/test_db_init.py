"""
测试数据库初始化
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from algomate.data.database import Database

def test_database_init():
    """测试数据库初始化"""
    print("=" * 60)
    print("测试数据库初始化...")
    print("=" * 60)
    
    try:
        db = Database.get_instance()
        print("[OK] 数据库初始化成功")
        
        session = db.get_session()
        print("[OK] 获取会话成功")
        session.close()
        
        print("\n[SUCCESS] 数据库初始化测试通过！")
        return True
    except Exception as e:
        print(f"[FAIL] 数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_database_init()
    sys.exit(0 if success else 1)
