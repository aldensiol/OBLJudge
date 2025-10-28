from pydantic import BaseModel, Field


class MetricScore(BaseModel):
    score: int = Field(..., ge=0, le=10, description="Score from 0-10 for this metric")
    justification: str = Field(
        ...,
        description="Brief explanation for the score based on URL and content analysis",
    )


class LinkMetrics(BaseModel):
    source_credibility: MetricScore = Field(
        ..., description="Credibility of the source domain and content quality"
    )
    recency_and_currency: MetricScore = Field(
        ..., description="Publication date recency from content metadata"
    )
    anchor_text_quality: MetricScore = Field(
        ...,
        description="Quality and accuracy of anchor text relative to actual content",
    )
    topical_relevance: MetricScore = Field(
        ..., description="Relevance of linked content to article topic"
    )
    integration_placement_quality: MetricScore = Field(
        ..., description="Natural integration and content support for placement"
    )
    user_trust_eeat_alignment: MetricScore = Field(
        ..., description="Source authority and expertise verified from content"
    )
    contextual_value_contribution: MetricScore = Field(
        ..., description="Actual informational value from the linked content"
    )
    link_necessity: MetricScore = Field(
        ..., description="Whether the link is necessary for the article"
    )


class JudgeOutput(BaseModel):
    link_url: str = Field(..., description="The URL of the evaluated hyperlink")
    metrics: LinkMetrics = Field(
        ...,
        description="Individual metric scores for this link based on URL and content",
    )
    overall_score: float = Field(
        ...,
        ge=0,
        le=10,
        description="Average score across all metrics for this link",
    )
