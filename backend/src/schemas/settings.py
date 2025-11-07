"""
애플리케이션 설정 스키마

데이터베이스에 저장되는 동적 설정을 관리합니다.
관리자가 UI에서 변경 가능한 설정들을 포함합니다.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


class LLMProviderConfig(BaseModel):
    """LLM Provider 설정"""
    name: str = Field(..., description="Provider 이름 (openai, anthropic)")
    api_key: str = Field(..., description="API Key (암호화하여 저장)")
    model: str = Field(..., description="기본 모델명")
    enabled: bool = Field(default=True, description="활성화 여부")
    timeout: int = Field(default=30, description="타임아웃 (초)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "openai",
                "api_key": "sk-...",
                "model": "gpt-4o-mini",
                "enabled": True,
                "timeout": 30
            }
        }


class AdminSettings(BaseModel):
    """관리자 설정"""
    admin_emails: List[EmailStr] = Field(
        default_factory=list,
        description="관리자 권한을 가진 이메일 목록"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "admin_emails": ["admin@example.com", "manager@example.com"]
            }
        }


class AISettings(BaseModel):
    """AI 설정"""
    provider_priority: List[str] = Field(
        default=["openai", "anthropic"],
        description="AI Provider 우선순위 (앞에 있을수록 먼저 시도)"
    )
    providers: List[LLMProviderConfig] = Field(
        default_factory=list,
        description="LLM Provider 설정 목록"
    )
    default_timeout: int = Field(
        default=30,
        description="기본 타임아웃 (초)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "provider_priority": ["openai", "anthropic"],
                "providers": [
                    {
                        "name": "openai",
                        "api_key": "sk-...",
                        "model": "gpt-4o-mini",
                        "enabled": True,
                        "timeout": 30
                    },
                    {
                        "name": "anthropic",
                        "api_key": "sk-ant-...",
                        "model": "claude-3-5-sonnet-20241022",
                        "enabled": True,
                        "timeout": 30
                    }
                ],
                "default_timeout": 30
            }
        }


class AppSettings(BaseModel):
    """애플리케이션 전체 설정"""
    id: str = Field(default="app_settings", description="설정 문서 ID (고정)")
    admin: AdminSettings = Field(default_factory=AdminSettings)
    ai: AISettings = Field(default_factory=AISettings)
    updated_at: Optional[datetime] = Field(None, description="마지막 수정 시간")
    updated_by: Optional[str] = Field(None, description="마지막 수정한 사용자 ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "app_settings",
                "admin": {
                    "admin_emails": ["admin@example.com"]
                },
                "ai": {
                    "provider_priority": ["openai", "anthropic"],
                    "providers": [],
                    "default_timeout": 30
                },
                "updated_at": "2025-11-01T10:00:00Z",
                "updated_by": "user-123"
            }
        }


class UpdateAdminSettingsRequest(BaseModel):
    """관리자 설정 업데이트 요청"""
    admin_emails: List[EmailStr] = Field(
        ...,
        description="관리자 이메일 목록"
    )


class UpdateAISettingsRequest(BaseModel):
    """AI 설정 업데이트 요청"""
    provider_priority: Optional[List[str]] = Field(
        None,
        description="Provider 우선순위"
    )
    providers: Optional[List[LLMProviderConfig]] = Field(
        None,
        description="Provider 설정 목록"
    )
    default_timeout: Optional[int] = Field(
        None,
        ge=5,
        le=120,
        description="기본 타임아웃 (5-120초)"
    )


class SettingsResponse(BaseModel):
    """설정 조회 응답"""
    admin: AdminSettings
    ai: AISettings
    updated_at: Optional[datetime]
    updated_by: Optional[str]
    
    class Config:
        json_schema_extra = {
            "example": {
                "admin": {
                    "admin_emails": ["admin@example.com"]
                },
                "ai": {
                    "provider_priority": ["openai", "anthropic"],
                    "providers": [
                        {
                            "name": "openai",
                            "api_key": "sk-***",  # Masked
                            "model": "gpt-4o-mini",
                            "enabled": True,
                            "timeout": 30
                        }
                    ],
                    "default_timeout": 30
                },
                "updated_at": "2025-11-01T10:00:00Z",
                "updated_by": "user-123"
            }
        }

