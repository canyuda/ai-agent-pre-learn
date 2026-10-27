"""t5：多模型关联 —— 设计一个 AgentPipeline 模型：

- steps：一个 PipelineStep 列表。每个步骤有 name、tool（ToolDefinition 类型）、
  depends_on（字符串列表，代表依赖的前置步骤）
- 用 @model_validator 检查：depends_on 里引用的步骤名必须在 steps 中存在
"""
from pydantic import BaseModel, Field, ValidationError, model_validator

from t4 import ToolDefinition


class PipelineStep(BaseModel):
    name: str = Field(min_length=1)
    tool: ToolDefinition
    depends_on: list[str] = Field(default_factory=list)


class AgentPipeline(BaseModel):
    steps: list[PipelineStep] = Field(min_length=1)

    @model_validator(mode="after")
    def check_deps_exist(self) -> "AgentPipeline":
        names = {s.name for s in self.steps}
        for step in self.steps:
            missing = set(step.depends_on) - names
            if missing:
                raise ValueError(f"步骤 {step.name!r} 依赖了不存在的步骤: {sorted(missing)}")
        return self


weather = ToolDefinition(
    name="get_weather", description="查询天气",
    parameters={"type": "object", "properties": {"city": {"type": "string"}}},
)
report = ToolDefinition(
    name="make_report", description="生成报告",
    parameters={"type": "object", "properties": {"text": {"type": "string"}}},
)

ok = AgentPipeline(steps=[
    PipelineStep(name="fetch", tool=weather),
    PipelineStep(name="summarize", tool=report, depends_on=["fetch"]),
])
print(ok.model_dump_json(indent=2))

try:
    AgentPipeline(steps=[
        PipelineStep(name="fetch", tool=weather),
        PipelineStep(name="summarize", tool=report, depends_on=["fetch", "notify"]),
    ])
except ValidationError as e:
    print(f"\n{e}")
