"""정적 사주 참조 테이블 (side_projects domain/constants + 표시용 영문 라벨)."""

from __future__ import annotations

from typing import Dict, List, Set

ELEMENTS: List[str] = ["wood", "fire", "earth", "metal", "water"]

STEM_TO_ELEMENT: Dict[str, str] = {
    "甲": "wood",
    "乙": "wood",
    "丙": "fire",
    "丁": "fire",
    "戊": "earth",
    "己": "earth",
    "庚": "metal",
    "辛": "metal",
    "壬": "water",
    "癸": "water",
}

STEM_TO_POLARITY: Dict[str, str] = {
    "甲": "yang",
    "乙": "yin",
    "丙": "yang",
    "丁": "yin",
    "戊": "yang",
    "己": "yin",
    "庚": "yang",
    "辛": "yin",
    "壬": "yang",
    "癸": "yin",
}

STEM_TO_KOREAN: Dict[str, str] = {
    "甲": "갑목",
    "乙": "을목",
    "丙": "병화",
    "丁": "정화",
    "戊": "무토",
    "己": "기토",
    "庚": "경금",
    "辛": "신금",
    "壬": "임수",
    "癸": "계수",
}

STEM_TO_ENGLISH_LABEL: Dict[str, str] = {
    "甲": "Gap Wood",
    "乙": "Eul Wood",
    "丙": "Byeong Fire",
    "丁": "Jeong Fire",
    "戊": "Mu Earth",
    "己": "Gi Earth",
    "庚": "Gyeong Metal",
    "辛": "Sin Metal",
    "壬": "Im Water",
    "癸": "Gye Water",
}

GAN_TO_STEM_ROMAN: Dict[str, str] = {
    "甲": "Jia",
    "乙": "Yi",
    "丙": "Bing",
    "丁": "Ding",
    "戊": "Wu",
    "己": "Ji",
    "庚": "Geng",
    "辛": "Xin",
    "壬": "Ren",
    "癸": "Gui",
}

ZHI_TO_BRANCH_EN: Dict[str, str] = {
    "子": "Rat",
    "丑": "Ox",
    "寅": "Tiger",
    "卯": "Rabbit",
    "辰": "Dragon",
    "巳": "Snake",
    "午": "Horse",
    "未": "Goat",
    "申": "Monkey",
    "酉": "Rooster",
    "戌": "Dog",
    "亥": "Pig",
}

BRANCH_TO_PRIMARY_ELEMENT: Dict[str, str] = {
    "子": "water",
    "丑": "earth",
    "寅": "wood",
    "卯": "wood",
    "辰": "earth",
    "巳": "fire",
    "午": "fire",
    "未": "earth",
    "申": "metal",
    "酉": "metal",
    "戌": "earth",
    "亥": "water",
}

BRANCH_TO_HIDDEN_STEMS: Dict[str, List[str]] = {
    "子": ["癸"],
    "丑": ["己", "癸", "辛"],
    "寅": ["甲", "丙", "戊"],
    "卯": ["乙"],
    "辰": ["戊", "乙", "癸"],
    "巳": ["丙", "庚", "戊"],
    "午": ["丁", "己"],
    "未": ["己", "丁", "乙"],
    "申": ["庚", "壬", "戊"],
    "酉": ["辛"],
    "戌": ["戊", "辛", "丁"],
    "亥": ["壬", "甲"],
}

GENERATES: Dict[str, str] = {
    "wood": "fire",
    "fire": "earth",
    "earth": "metal",
    "metal": "water",
    "water": "wood",
}

GENERATED_BY: Dict[str, str] = {value: key for key, value in GENERATES.items()}

CONTROLS: Dict[str, str] = {
    "wood": "earth",
    "fire": "metal",
    "earth": "water",
    "metal": "wood",
    "water": "fire",
}

CONTROLLED_BY: Dict[str, str] = {value: key for key, value in CONTROLS.items()}

BRANCH_CLASH_PAIRS: Set[frozenset[str]] = {
    frozenset({"子", "午"}),
    frozenset({"丑", "未"}),
    frozenset({"寅", "申"}),
    frozenset({"卯", "酉"}),
    frozenset({"辰", "戌"}),
    frozenset({"巳", "亥"}),
}
