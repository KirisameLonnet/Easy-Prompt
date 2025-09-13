"""
Supabase配置模块
"""
import os
from supabase import create_client, Client
from typing import Optional

class SupabaseConfig:
    """Supabase配置管理器"""
    
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_ANON_KEY")
        self.service_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL 和 SUPABASE_ANON_KEY 环境变量必须设置")
        
        self.client: Optional[Client] = None
        self._initialize_client()
    
    def _initialize_client(self):
        """初始化Supabase客户端"""
        try:
            self.client = create_client(self.url, self.key)
            print("✅ Supabase客户端初始化成功")
        except Exception as e:
            print(f"❌ Supabase客户端初始化失败: {e}")
            raise
    
    def get_client(self) -> Client:
        """获取Supabase客户端"""
        if not self.client:
            self._initialize_client()
        return self.client
    
    def get_service_client(self) -> Client:
        """获取服务端Supabase客户端（使用service key）"""
        if not self.service_key:
            raise ValueError("SUPABASE_SERVICE_KEY 环境变量未设置")
        return create_client(self.url, self.service_key)

# 全局配置实例
try:
    supabase_config = SupabaseConfig()
except ValueError as e:
    print(f"⚠️ 警告: Supabase配置初始化失败: {e}")
    print("请设置SUPABASE_URL和SUPABASE_ANON_KEY环境变量")
    supabase_config = None
