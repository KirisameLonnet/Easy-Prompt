"""
Pydantic schemas for FastAPI session management
符合FastAPI规范的会话管理数据模型
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum


class SessionStatus(str, Enum):
    """会话状态枚举"""
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    ERROR = "error"
    PROMPT_GENERATED = "prompt_generated"  # 已生成提示词但可继续对话


class MessageType(str, Enum):
    """消息类型枚举"""
    SYSTEM = "system"
    AI = "ai"
    USER = "user"
    FINAL_PROMPT = "final_prompt"
    ERROR = "error"


class ApiType(str, Enum):
    """API类型枚举"""
    OPENAI = "openai"
    GEMINI = "gemini"


class ChatMessage(BaseModel):
    """聊天消息模型"""
    id: str = Field(..., description="消息唯一标识")
    type: MessageType = Field(..., description="消息类型")
    content: str = Field(..., description="消息内容")
    timestamp: datetime = Field(default_factory=datetime.now, description="消息时间戳")
    is_complete: bool = Field(default=True, description="消息是否完整")


class EvaluationData(BaseModel):
    """评估数据模型"""
    evaluation_status: str = Field(default="", description="评估状态")
    show_evaluation_card: bool = Field(default=False, description="是否显示评估卡片")
    extracted_traits: List[str] = Field(default_factory=list, description="提取的角色特征")
    extracted_keywords: List[str] = Field(default_factory=list, description="提取的关键词")
    evaluation_score: Optional[float] = Field(default=None, description="评估分数")
    completeness_data: Dict[str, float] = Field(
        default_factory=lambda: {
            "core_identity": 0.0,
            "personality_traits": 0.0,
            "behavioral_patterns": 0.0,
            "interaction_patterns": 0.0
        },
        description="完整度分解数据"
    )
    evaluation_suggestions: List[str] = Field(default_factory=list, description="改进建议")
    final_prompt_content: str = Field(default="", description="最终提示词内容")
    show_prompt_result: bool = Field(default=False, description="是否显示提示词结果")
    prompt_timestamp: datetime = Field(default_factory=datetime.now, description="提示词生成时间")


class Session(BaseModel):
    """会话模型"""
    id: str = Field(..., description="会话唯一标识")
    name: str = Field(..., description="会话名称")
    user_id: Optional[str] = Field(default=None, description="关联用户ID（None表示匿名）")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="最后更新时间")
    message_count: int = Field(default=0, description="消息数量")
    status: SessionStatus = Field(default=SessionStatus.ACTIVE, description="会话状态")
    last_message: Optional[str] = Field(default=None, description="最后一条消息")
    messages: List[ChatMessage] = Field(default_factory=list, description="消息列表")
    evaluation_data: Optional[EvaluationData] = Field(default=None, description="评估数据")
    
    # 未来扩展：访问控制
    is_public: bool = Field(default=False, description="是否公开（用于分享）")
    shared_with: List[str] = Field(default_factory=list, description="共享给的用户ID列表")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ApiConfig(BaseModel):
    """API配置模型"""
    api_type: ApiType = Field(..., description="API类型")
    api_key: Optional[str] = Field(default=None, description="API密钥")
    base_url: Optional[str] = Field(default=None, description="基础URL")
    model: Optional[str] = Field(default=None, description="模型名称")
    evaluator_model: Optional[str] = Field(default=None, description="评估模型名称")
    temperature: float = Field(default=0.7, description="温度参数")
    max_tokens: int = Field(default=4000, description="最大令牌数")
    nsfw_mode: bool = Field(default=False, description="NSFW模式")


class SessionCreate(BaseModel):
    """创建会话请求模型"""
    name: Optional[str] = Field(default=None, description="会话名称，为空则自动生成")
    api_config: Optional[ApiConfig] = Field(default=None, description="API配置")


class SessionUpdate(BaseModel):
    """更新会话请求模型"""
    name: Optional[str] = Field(default=None, description="会话名称")
    status: Optional[SessionStatus] = Field(default=None, description="会话状态")


class SessionResponse(BaseModel):
    """会话响应模型"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[Union[Session, List[Session]]] = Field(default=None, description="响应数据")


class WebSocketMessage(BaseModel):
    """WebSocket消息模型"""
    type: str = Field(..., description="消息类型")
    payload: Dict[str, Any] = Field(..., description="消息载荷")


class UserResponse(BaseModel):
    """用户响应模型"""
    answer: str = Field(..., description="用户回答")


class UserConfirmation(BaseModel):
    """用户确认模型"""
    confirm: bool = Field(..., description="是否确认")


class ApiConfigResult(BaseModel):
    """API配置结果模型"""
    success: bool = Field(..., description="配置是否成功")
    message: str = Field(..., description="结果消息")


class EvaluationUpdate(BaseModel):
    """评估更新模型"""
    message: str = Field(..., description="评估消息")
    extracted_traits: Optional[List[str]] = Field(default=None, description="提取的特征")
    extracted_keywords: Optional[List[str]] = Field(default=None, description="提取的关键词")
    evaluation_score: Optional[float] = Field(default=None, description="评估分数")
    completeness_breakdown: Optional[Dict[str, float]] = Field(default=None, description="完整度分解")
    suggestions: Optional[List[str]] = Field(default=None, description="建议")
    is_ready: Optional[bool] = Field(default=None, description="是否准备就绪")
