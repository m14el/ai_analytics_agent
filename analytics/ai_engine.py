"""
AI Analytics Agent — AI Analysis Engine
Integrates with OpenAI/Anthropic for hypothesis generation and recommendations.
Falls back to rule-based analysis when no AI provider is configured.
"""
import json
import logging
from typing import Dict, List, Optional
import pandas as pd
from config import settings
from models.schemas import AIAnalysisResult, AIHypothesis, AIRecommendation

logger = logging.getLogger(__name__)


def _build_context(data: Dict[str, pd.DataFrame], anomalies: List[dict]) -> str:
    """Build a text context for the AI model from analytics data."""
    lines = ["# Аналитические данные компании\n"]

    # Project summary
    if "project_metrics" in data:
        pm = data["project_metrics"]
        lines.append("## Проекты")
        for _, r in pm.iterrows():
            status = "🟢" if r.get("profitability_status") == "green" else "🟡" if r.get("profitability_status") == "yellow" else "🔴"
            lines.append(f"- {status} {r['name']} ({r.get('stack','N/A')}): маржа={r.get('margin',0):.1f}%, доход=${r.get('total_revenue',0):,.0f}, расходы=${r.get('total_costs',0):,.0f}")
        lines.append("")

    # Stack summary
    if "stack_metrics" in data:
        lines.append("## Стеки технологий")
        for _, r in data["stack_metrics"].iterrows():
            lines.append(f"- {r['stack']}: проектов={r.get('project_count',0)}, маржа={r.get('margin',0):.1f}%, доход=${r.get('total_revenue',0):,.0f}")
        lines.append("")

    # Anomalies
    if anomalies:
        lines.append("## Обнаруженные аномалии")
        for a in anomalies[:15]:
            lines.append(f"- [{a.get('severity','?').upper()}] {a.get('description','')}")
        lines.append("")

    # Task summary
    if "task_type_metrics" in data:
        lines.append("## Типы задач")
        for _, r in data["task_type_metrics"].iterrows():
            lines.append(f"- {r['task_type']}: задач={r.get('task_count',0)}, перерасход={r.get('overtime_ratio',0):.2f}x, reopens={r.get('reopen_rate',0):.2f}")

    return "\n".join(lines)


SYSTEM_PROMPT = """Ты — AI-аналитик прибыльности IT-компании. Твоя задача:
1. Проанализировать финансовые и производственные данные
2. Выявить убыточные проекты, стеки и процессы
3. Сформулировать гипотезы о причинах потерь
4. Предложить конкретные рекомендации по оптимизации

Отвечай строго в JSON-формате:
{
  "summary": "краткое резюме анализа",
  "hypotheses": [
    {"title": "...", "description": "...", "confidence": 0.0-1.0, "affected_metrics": [...], "source_data": [...], "severity": "low|medium|high|critical"}
  ],
  "recommendations": [
    {"category": "process|stack|management", "title": "...", "description": "...", "expected_impact": "...", "affected_metrics": [...], "priority": "low|medium|high|critical"}
  ]
}"""


async def _call_openai(context: str) -> Optional[dict]:
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        resp = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": context},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        return json.loads(resp.choices[0].message.content)
    except Exception as e:
        logger.error(f"OpenAI call failed: {e}")
        return None


async def _call_anthropic(context: str) -> Optional[dict]:
    try:
        from anthropic import AsyncAnthropic
        client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        resp = await client.messages.create(
            model=settings.anthropic_model,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": context}],
        )
        text = resp.content[0].text
        start = text.find("{")
        end = text.rfind("}") + 1
        return json.loads(text[start:end]) if start >= 0 else None
    except Exception as e:
        logger.error(f"Anthropic call failed: {e}")
        return None


def _rule_based_analysis(data: Dict[str, pd.DataFrame], anomalies: List[dict]) -> dict:
    """Fallback rule-based analysis when no AI provider is configured."""
    hypotheses, recommendations = [], []
    pm = data.get("project_metrics", pd.DataFrame())

    # Loss-making projects
    if len(pm) > 0 and "margin" in pm.columns:
        loss = pm[pm["margin"] < 0]
        if len(loss) > 0:
            names = ", ".join(loss["name"].tolist()[:5])
            hypotheses.append({
                "title": "Убыточные проекты", "confidence": 0.95, "severity": "high",
                "description": f"Проекты {names} работают в убыток. Расходы превышают доходы.",
                "affected_metrics": ["profitability", "margin"],
                "source_data": [f"{r['name']}: маржа {r['margin']:.1f}%" for _, r in loss.iterrows()],
            })
            recommendations.append({
                "category": "management", "title": "Пересмотр убыточных проектов",
                "description": "Провести ревью убыточных проектов: пересмотреть ценообразование или сократить расходы.",
                "expected_impact": "Потенциальное сокращение потерь на 20-40%",
                "affected_metrics": ["profitability", "margin"], "priority": "high",
            })

    # High overtime tasks
    overtime_anomalies = [a for a in anomalies if a["type"] == "task_overtime"]
    if overtime_anomalies:
        hypotheses.append({
            "title": "Систематический перерасход часов", "confidence": 0.8, "severity": "high",
            "description": f"Обнаружено {len(overtime_anomalies)} задач с перерасходом >2x. Возможные причины: неточные оценки, частые изменения требований.",
            "affected_metrics": ["burn_rate", "estimation_accuracy"],
            "source_data": [a["description"] for a in overtime_anomalies[:5]],
        })
        recommendations.append({
            "category": "process", "title": "Улучшить процесс оценки задач",
            "description": "Внедрить planning poker, декомпозицию задач, исторические данные для оценок.",
            "expected_impact": "Снижение перерасхода на 30%",
            "affected_metrics": ["estimation_accuracy", "burn_rate"], "priority": "high",
        })

    # High reopens
    reopen_anomalies = [a for a in anomalies if a["type"] == "task_high_reopen"]
    if reopen_anomalies:
        hypotheses.append({
            "title": "Проблемы с качеством или требованиями", "confidence": 0.75, "severity": "medium",
            "description": f"{len(reopen_anomalies)} задач с высоким числом переоткрытий. Возможен communication overhead.",
            "affected_metrics": ["reopen_rate", "velocity"],
            "source_data": [a["description"] for a in reopen_anomalies[:5]],
        })
        recommendations.append({
            "category": "process", "title": "Внедрить Definition of Done",
            "description": "Стандартизировать критерии приёмки задач, внедрить code review checklist.",
            "expected_impact": "Снижение reopen rate на 50%",
            "affected_metrics": ["reopen_rate", "velocity"], "priority": "medium",
        })

    # Stack analysis
    sm = data.get("stack_metrics", pd.DataFrame())
    if len(sm) > 0 and "margin" in sm.columns:
        bad_stacks = sm[sm["margin"] < 0]
        if len(bad_stacks) > 0:
            for _, s in bad_stacks.iterrows():
                hypotheses.append({
                    "title": f"Убыточный стек: {s['stack']}", "confidence": 0.85, "severity": "high",
                    "description": f"Стек {s['stack']} работает с отрицательной маржей ({s['margin']:.1f}%). Возможные причины: высокие ставки, сложность, недостаток экспертизы.",
                    "affected_metrics": ["stack_profitability"], "source_data": [f"{s['stack']}: маржа {s['margin']:.1f}%"],
                })
            recommendations.append({
                "category": "stack", "title": "Оптимизация убыточных стеков",
                "description": "Пересмотреть ценообразование для убыточных стеков или инвестировать в повышение экспертизы.",
                "expected_impact": "Выход убыточных стеков на безубыточность",
                "affected_metrics": ["stack_profitability"], "priority": "high",
            })

    summary = f"Анализ выявил {len(hypotheses)} гипотез и {len(recommendations)} рекомендаций. "
    loss_count = len(pm[pm['margin'] < 0]) if len(pm) > 0 and 'margin' in pm.columns else 0
    summary += f"Убыточных проектов: {loss_count} из {len(pm)}. Обнаружено {len(anomalies)} аномалий."

    return {"summary": summary, "hypotheses": hypotheses, "recommendations": recommendations}


async def run_analysis(data: Dict[str, pd.DataFrame], anomalies: List[dict]) -> AIAnalysisResult:
    """Run AI analysis — uses configured provider or falls back to rule-based."""
    logger.info(f"Running AI analysis (provider: {settings.ai_provider})...")
    context = _build_context(data, anomalies)
    result = None

    if settings.ai_provider == "openai" and settings.openai_api_key:
        result = await _call_openai(context)
    elif settings.ai_provider == "anthropic" and settings.anthropic_api_key:
        result = await _call_anthropic(context)

    if result is None:
        logger.info("  Using rule-based analysis (no AI provider configured)")
        result = _rule_based_analysis(data, anomalies)

    return AIAnalysisResult(
        summary=result.get("summary", ""),
        hypotheses=[AIHypothesis(**h) for h in result.get("hypotheses", [])],
        recommendations=[AIRecommendation(**r) for r in result.get("recommendations", [])],
        anomalies=anomalies,
    )
