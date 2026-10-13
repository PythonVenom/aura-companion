"""Mentor Skills Branches — art, medicine, business, languages.
Наука: T-shaped skills (Guest 1991), Career Graph.
"""
from aura.kernel.agents.mentor.schema import Skill

# ═══ ART (10) ═══
SKILLS_ART = [
    Skill("draw-basics", "Рисунок: основы", 1, "art",
          [], 20, []),
    Skill("draw-anatomy", "Рисунок: анатомия", 2, "art",
          ["draw-basics"], 30, []),
    Skill("color-theory", "Цвет: теория", 2, "art",
          ["draw-basics"], 15, []),
    Skill("photoshop", "Photoshop: базы", 3, "art",
          ["color-theory"], 20, []),
    Skill("krita", "Krita: цифровой рисунок", 3, "art",
          ["draw-anatomy", "color-theory"], 20, []),
    Skill("design-ui", "UI/UX дизайн", 3, "art",
          ["color-theory"], 25, []),
    Skill("figma", "Figma", 3, "art",
          ["design-ui"], 15, []),
    Skill("3d-blender", "Blender 3D", 4, "art",
          ["krita"], 40, []),
    Skill("animation", "Анимация", 4, "art",
          ["3d-blender"], 30, []),
    Skill("art-direction", "Арт-директор", 5, "art",
          ["animation", "design-ui"], 50, []),
]

# ═══ MEDICINE (8) ═══
SKILLS_MEDICINE = [
    Skill("anatomy-basics", "Анатомия: основы", 1, "medicine",
          [], 30, []),
    Skill("first-aid", "Первая помощь", 1, "medicine",
          [], 10, []),
    Skill("pharmacology", "Фармакология", 3, "medicine",
          ["anatomy-basics"], 40, []),
    Skill("diagnostics", "Диагностика", 4, "medicine",
          ["anatomy-basics", "pharmacology"], 50, []),
    Skill("geriatrics", "Гериатрия", 4, "medicine",
          ["diagnostics"], 40, []),
    Skill("emergency-med", "Неотложка", 4, "medicine",
          ["first-aid"], 30, []),
    Skill("rehab", "Реабилитация", 4, "medicine",
          ["geriatrics"], 30, []),
    Skill("care-planning", "Планы ухода", 5, "medicine",
          ["rehab"], 25, []),
]

# ═══ BUSINESS (6) ═══
SKILLS_BUSINESS = [
    Skill("biz-model", "Бизнес-модели", 2, "business",
          [], 15, []),
    Skill("marketing", "Маркетинг", 2, "business",
          [], 20, []),
    Skill("sales", "Продажи", 2, "business",
          [], 15, []),
    Skill("finance", "Финансы", 3, "business",
          ["biz-model"], 25, []),
    Skill("product", "Product management", 4, "business",
          ["marketing", "finance"], 30, []),
    Skill("ceo", "CEO", 5, "business",
          ["product", "sales"], 50, []),
]

# ═══ LANGUAGES (6) ═══
SKILLS_LANGUAGES = [
    Skill("english-a1", "English A1", 1, "lang", [], 40, []),
    Skill("english-b1", "English B1", 2, "lang",
          ["english-a1"], 60, []),
    Skill("english-c1", "English C1", 4, "lang",
          ["english-b1"], 80, []),
    Skill("chinese-hsk1", "Китайский HSK1", 1, "lang", [], 50, []),
    Skill("chinese-hsk3", "Китайский HSK3", 3, "lang",
          ["chinese-hsk1"], 80, []),
    Skill("spanish-a1", "Испанский A1", 1, "lang", [], 40, []),
]

ALL_BRANCHES = SKILLS_ART + SKILLS_MEDICINE + SKILLS_BUSINESS + SKILLS_LANGUAGES
