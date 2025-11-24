#!/usr/bin/env python3
"""轻量验证搜索助手的概念检测能力"""

import sys
from pathlib import Path

# 确保可以导入项目根目录模块
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from search_helper import search_helper

def test_detect_concept_query_basic():
    message = "什么是魔法现实主义？我不太熟悉。"
    result = search_helper.detect_concept_query(message)
    assert result is not None
    assert result["concept_name"] == "魔法现实主义"


def test_detect_concept_query_english():
    message = "Can you explain neural style transfer in simple words?"
    result = search_helper.detect_concept_query(message)
    assert result is not None
    assert "neural style transfer" in result["concept_name"].lower()


def test_detect_concept_query_non_match():
    message = "我想要一个傲娇女仆角色的设定，包含她的日常爱好。"
    result = search_helper.detect_concept_query(message)
    assert result is None


def test_plan_detects_character_need():
    message = "能帮我查一下雷电将军这个角色的背景吗？"
    plan = search_helper.plan_search_strategy(message)
    assert plan["should_search"] is True
    assert plan["intent_type"] == "character"
    assert "雷电将军" in plan["query"]


def test_plan_skips_pure_creation():
    message = "我想创建一个傲娇女仆角色设定，帮我一起完善。"
    plan = search_helper.plan_search_strategy(message)
    assert plan["should_search"] is False


def test_plan_handles_direct_search_command():
    message = "你连网搜索一下丰川祥子"
    plan = search_helper.plan_search_strategy(message)
    assert plan["should_search"] is True
    assert plan["intent_type"] == "character"
    assert "丰川祥子" in plan["query"]


def test_plan_handles_do_you_know_question():
    message = "你知道丰川祥子吗"
    plan = search_helper.plan_search_strategy(message)
    assert plan["should_search"] is True
    assert plan["intent_type"] == "character"
    assert plan["query"].startswith("丰川祥子")


if __name__ == "__main__":
    test_detect_concept_query_basic()
    test_detect_concept_query_english()
    test_detect_concept_query_non_match()
    test_plan_detects_character_need()
    test_plan_skips_pure_creation()
    test_plan_handles_direct_search_command()
    test_plan_handles_do_you_know_question()
    print("✅ 概念检测测试通过")
