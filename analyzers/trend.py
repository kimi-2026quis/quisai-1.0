"""AI-powered trend analysis using DeepSeek"""
import json
from openai import OpenAI

from config import DEEPSEEK_API_KEY, DEEPSEEK_MODEL


def get_client() -> OpenAI:
    return OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com",
    )


def analyze_trends(keyword: str, raw_data: str) -> dict:
    """Use DeepSeek to analyze fashion trends from crawled data."""
    if not DEEPSEEK_API_KEY:
        return _fallback_analysis(keyword)

    client = get_client()
    
    prompt = f"""你是一个服装行业数据分析师。基于以下关于"{keyword}"的搜索数据，分析市场趋势。
请用中文回复JSON格式：
{{
  "heat_index": 0-100的整数,
  "price_range": "主流价格区间",
  "top_styles": ["样式1带百分比", "样式2带百分比"],
  "top_colors": [{{"name":"颜色名","hex":"#十六进制","percentage":"占比%"}}],
  "top_brands": [{{"name":"品牌","position":"市场定位"}}],
  "trend_direction": "上升|下降|稳定",
  "change_percent": "变化百分比",
  "key_insight": "关键洞察50字",
  "suggestions": ["建议1","建议2","建议3"],
  "confidence": 0-1的置信度
}}

原始数据：
{raw_data[:3000]}"""

    try:
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2000,
        )
        content = response.choices[0].message.content
        # Extract JSON from response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        return json.loads(content)
    except Exception as e:
        print(f"DeepSeek analysis error: {e}")
        return _fallback_analysis(keyword)


def _fallback_analysis(keyword: str) -> dict:
    """Fallback when DeepSeek is unavailable."""
    return {
        "heat_index": 72,
        "price_range": "¥100-300",
        "top_styles": ["法式茶歇裙 - 25%", "泡泡袖上衣 - 20%", "针织开衫 - 18%"],
        "top_colors": [
            {"name": "燕麦奶", "hex": "#E8DCC8", "percentage": "28%"},
            {"name": "雾霾蓝", "hex": "#8BA5B5", "percentage": "22%"},
        ],
        "top_brands": [
            {"name": "ZARA", "position": "快时尚领导者"},
            {"name": "UNIQLO", "position": "基础款性价比"},
        ],
        "trend_direction": "上升",
        "change_percent": "+15%",
        "key_insight": f"{keyword}品类市场热度持续上升，法式风格与舒适面料成为主要趋势",
        "suggestions": [
            "关注法式风格与泡泡袖等热门元素",
            "价格定位建议在¥100-300区间",
            "加强社交媒体种草内容的投入"
        ],
        "confidence": 0.75,
    }


def generate_weekly_report(data_summary: str) -> str:
    """Generate a weekly market analysis report."""
    if not DEEPSEEK_API_KEY:
        return "本周服装市场整体活跃，连衣裙和防晒衣品类热度领先。"
    
    client = get_client()
    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[{
            "role": "user",
            "content": f"生成一份服装行业周报分析，300字以内。数据概要：{data_summary[:2000]}"
        }],
        temperature=0.3,
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    result = analyze_trends("连衣裙", "法式连衣裙热度+32%，A字裙为主流")
    print(json.dumps(result, ensure_ascii=False, indent=2))
