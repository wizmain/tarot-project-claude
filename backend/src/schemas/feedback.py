"""
피드백 Pydantic 스키마 정의 모듈

이 모듈의 목적:
- API 요청/응답에 사용할 피드백 데이터 검증 스키마
- 데이터베이스 모델과 API 간의 변환
- 입력 데이터 유효성 검사 (rating 1-5 등)

주요 스키마:
- FeedbackCreate: 피드백 생성 요청
- FeedbackUpdate: 피드백 수정 요청
- FeedbackResponse: API 응답용 피드백 정보

사용 예시:
    # 피드백 생성 요청
    feedback_data = FeedbackCreate(
        rating=5,
        comment="매우 정확한 리딩이었습니다!",
        helpful=True,
        accurate=True
    )

    # 응답
    response = FeedbackResponse.from_orm(db_feedback)

TASK 참조:
- TASK-036: 피드백 제출 API
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class FeedbackCreate(BaseModel):
    """
    피드백 생성 요청 스키마

    Attributes:
        rating (int): 별점 평가 (1-5 필수)
        comment (str | None): 사용자 코멘트 (선택사항, 최대 1000자)
        helpful (bool): 리딩이 유용했는지 여부 (기본값 True)
        accurate (bool): 리딩이 정확했는지 여부 (기본값 True)
    """
    rating: int = Field(
        ...,
        ge=1,
        le=5,
        description="별점 평가 (1-5)"
    )
    comment: Optional[str] = Field(
        None,
        max_length=1000,
        description="사용자 코멘트 (선택사항)"
    )
    helpful: bool = Field(
        default=True,
        description="리딩이 유용했는지 여부"
    )
    accurate: bool = Field(
        default=True,
        description="리딩이 정확했는지 여부"
    )

    @field_validator('comment')
    @classmethod
    def validate_comment(cls, v: Optional[str]) -> Optional[str]:
        """
        코멘트 검증: 공백 문자열을 None으로 변환
        """
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "rating": 5,
                "comment": "매우 정확하고 도움이 되는 리딩이었습니다. 감사합니다!",
                "helpful": True,
                "accurate": True
            }
        }


class FeedbackUpdate(BaseModel):
    """
    피드백 수정 요청 스키마

    모든 필드가 선택사항 (부분 업데이트 지원)
    """
    rating: Optional[int] = Field(
        None,
        ge=1,
        le=5,
        description="별점 평가 (1-5)"
    )
    comment: Optional[str] = Field(
        None,
        max_length=1000,
        description="사용자 코멘트"
    )
    helpful: Optional[bool] = Field(
        None,
        description="리딩이 유용했는지 여부"
    )
    accurate: Optional[bool] = Field(
        None,
        description="리딩이 정확했는지 여부"
    )

    @field_validator('comment')
    @classmethod
    def validate_comment(cls, v: Optional[str]) -> Optional[str]:
        """
        코멘트 검증: 공백 문자열을 None으로 변환
        """
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "rating": 4,
                "comment": "수정된 피드백 코멘트입니다.",
                "helpful": True,
                "accurate": False
            }
        }


class FeedbackResponse(BaseModel):
    """
    피드백 응답 스키마

    Attributes:
        id (str): 피드백 고유 식별자
        reading_id (str): 연관된 리딩 ID
        user_id (str): 피드백 작성자 ID
        rating (int): 별점 평가 (1-5)
        comment (str | None): 사용자 코멘트
        helpful (bool): 리딩이 유용했는지 여부
        accurate (bool): 리딩이 정확했는지 여부
        created_at (datetime): 피드백 생성 시각
        updated_at (datetime): 피드백 수정 시각
    """
    id: str = Field(..., description="피드백 고유 식별자")
    reading_id: str = Field(..., description="연관된 리딩 ID")
    user_id: str = Field(..., description="피드백 작성자 ID")
    rating: int = Field(..., ge=1, le=5, description="별점 평가 (1-5)")
    comment: Optional[str] = Field(None, description="사용자 코멘트")
    helpful: bool = Field(..., description="리딩이 유용했는지 여부")
    accurate: bool = Field(..., description="리딩이 정확했는지 여부")
    created_at: datetime = Field(..., description="피드백 생성 시각")
    updated_at: datetime = Field(..., description="피드백 수정 시각")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "reading_id": "123e4567-e89b-12d3-a456-426614174001",
                "user_id": "123e4567-e89b-12d3-a456-426614174002",
                "rating": 5,
                "comment": "매우 정확하고 도움이 되는 리딩이었습니다.",
                "helpful": True,
                "accurate": True,
                "created_at": "2025-10-20T10:30:00",
                "updated_at": "2025-10-20T10:30:00"
            }
        }
