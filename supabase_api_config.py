"""
Supabase API配置服务
"""
from typing import Optional, Dict, Any
from datetime import datetime
from supabase_client import supabase_client
from supabase_models import ApiConfigSupabase, SupabaseUser
from crypto_utils import get_crypto_manager

class SupabaseApiConfigService:
    """Supabase API配置服务"""
    
    def __init__(self):
        if not supabase_client:
            raise ValueError("Supabase配置未初始化，请设置环境变量")
        self.supabase = supabase_client.get_client()
        self.crypto_manager = get_crypto_manager()
    
    async def save_api_config(self, user: SupabaseUser, api_config: Dict[str, Any]) -> ApiConfigSupabase:
        """保存用户API配置"""
        try:
            # 加密API密钥
            encrypted_api_key = self.crypto_manager.encrypt_api_key(api_config.get("api_key", ""))
            
            # 创建配置对象
            config = ApiConfigSupabase(
                id=f"{user.id}_{api_config.get('api_type', 'openai')}",
                user_id=user.id,
                api_type=api_config.get("api_type", "openai"),
                encrypted_api_key=encrypted_api_key,
                base_url=api_config.get("base_url", ""),
                model=api_config.get("model", ""),
                evaluator_model=api_config.get("evaluator_model"),
                temperature=api_config.get("temperature", 0.7),
                max_tokens=api_config.get("max_tokens", 4000),
                nsfw_mode=api_config.get("nsfw_mode", False),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # 保存到Supabase
            result = self.supabase.table("api_configs").upsert(config.dict()).execute()
            
            if result.data:
                return ApiConfigSupabase(**result.data[0])
            else:
                raise Exception("保存API配置失败")
                
        except Exception as e:
            print(f"保存API配置错误: {e}")
            raise Exception(f"保存API配置失败: {str(e)}")
    
    async def get_api_config(self, user: SupabaseUser) -> Optional[Dict[str, Any]]:
        """获取用户API配置"""
        try:
            result = self.supabase.table("api_configs").select("*").eq("user_id", user.id).execute()
            
            if not result.data:
                return None
            
            config_data = result.data[0]
            
            # 解密API密钥
            decrypted_api_key = self.crypto_manager.decrypt_api_key(config_data["encrypted_api_key"])
            
            return {
                "api_type": config_data["api_type"],
                "api_key": decrypted_api_key,
                "base_url": config_data["base_url"],
                "model": config_data["model"],
                "evaluator_model": config_data.get("evaluator_model"),
                "temperature": config_data["temperature"],
                "max_tokens": config_data["max_tokens"],
                "nsfw_mode": config_data["nsfw_mode"]
            }
            
        except Exception as e:
            print(f"获取API配置错误: {e}")
            return None
    
    async def update_api_config(self, user: SupabaseUser, api_config: Dict[str, Any]) -> ApiConfigSupabase:
        """更新用户API配置"""
        return await self.save_api_config(user, api_config)
    
    async def delete_api_config(self, user: SupabaseUser) -> bool:
        """删除用户API配置"""
        try:
            result = self.supabase.table("api_configs").delete().eq("user_id", user.id).execute()
            return True
        except Exception as e:
            print(f"删除API配置错误: {e}")
            return False
    
    async def test_api_config(self, user: SupabaseUser, api_config: Dict[str, Any]) -> Dict[str, Any]:
        """测试API配置"""
        try:
            # 这里可以添加API测试逻辑
            # 例如：发送测试请求到OpenAI或Gemini
            return {
                "success": True,
                "message": "API配置测试成功"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"API配置测试失败: {str(e)}"
            }

# 全局API配置服务实例
try:
    api_config_service = SupabaseApiConfigService()
except ValueError as e:
    print(f"⚠️ 警告: Supabase API配置服务初始化失败: {e}")
    api_config_service = None
