"""
搜索词生成器模块
生成有意义、上下文相关的搜索词，避免随机无意义搜索
"""

import logging
import random
from pathlib import Path

logger = logging.getLogger(__name__)


class SearchTermGenerator:
    """搜索词生成器类"""

    # 短语模板 - 用于生成有意义的搜索
    PHRASE_TEMPLATES = [
        "how to {}",
        "what is {}",
        "best {}",
        "top {}",
        "guide to {}",
        "tips for {}",
        "learn {}",
        "{} tutorial",
        "{} review",
        "{} explained",
        "why {}",
        "when to {}",
        "where to find {}",
        "benefits of {}",
        "history of {}",
    ]

    # 连接词 - 用于组合多个词
    CONNECTORS = [
        "and",
        "or",
        "vs",
        "versus",
        "with",
        "for",
        "in",
    ]

    def __init__(self, config):
        """
        初始化搜索词生成器

        Args:
            config: ConfigManager 实例
        """
        self.config = config
        self.base_terms: list[str] = []
        self.generated_phrases: list[str] = []
        self.used_terms: set[str] = set()

        # 加载搜索词文件
        terms_file = config.get("search.search_terms_file", "tools/search_terms.txt")
        self.load_terms_from_file(terms_file)

        # 生成短语组合
        self.generate_phrase_combinations(self.base_terms)

        logger.info(
            f"搜索词生成器初始化完成: {len(self.base_terms)} 基础词, {len(self.generated_phrases)} 生成短语"
        )

    def load_terms_from_file(self, file_path: str) -> list[str]:
        """
        从文件加载搜索词

        Args:
            file_path: 搜索词文件路径

        Returns:
            搜索词列表
        """
        try:
            if not Path(file_path).exists():
                logger.error(f"搜索词文件不存在: {file_path}")
                # 使用默认搜索词
                self.base_terms = self._get_default_terms()
                return self.base_terms

            with open(file_path, encoding="utf-8") as f:
                terms = [line.strip() for line in f if line.strip()]

            # 过滤掉单字符搜索词（太不自然）
            terms = [t for t in terms if len(t) > 1]

            if not terms:
                logger.warning(f"搜索词文件为空: {file_path}")
                self.base_terms = self._get_default_terms()
                return self.base_terms

            self.base_terms = terms
            logger.info(f"从文件加载了 {len(terms)} 个搜索词")
            return terms

        except Exception as e:
            logger.error(f"加载搜索词文件失败: {e}")
            self.base_terms = self._get_default_terms()
            return self.base_terms

    def _get_default_terms(self) -> list[str]:
        """获取默认搜索词"""
        return [
            "python programming",
            "machine learning",
            "web development",
            "data science",
            "artificial intelligence",
            "cloud computing",
            "cybersecurity",
            "mobile apps",
            "blockchain",
            "digital marketing",
        ]

    def generate_phrase_combinations(self, base_terms: list[str]) -> list[str]:
        """
        生成短语组合

        Args:
            base_terms: 基础搜索词列表

        Returns:
            生成的短语列表
        """
        phrases = []

        # 1. 使用模板生成短语
        for term in base_terms[:50]:  # 限制数量避免过多
            for template in self.PHRASE_TEMPLATES:
                phrase = template.format(term)
                phrases.append(phrase)

        # 2. 生成 "词 + 连接词 + 词" 组合
        for i, term1 in enumerate(base_terms[:30]):
            for term2 in base_terms[i + 1 : i + 6]:  # 限制组合数量
                if self._are_related(term1, term2):
                    # 直接组合
                    phrases.append(f"{term1} {term2}")

                    # 使用连接词
                    connector = random.choice(self.CONNECTORS)
                    phrases.append(f"{term1} {connector} {term2}")

        self.generated_phrases = phrases
        logger.info(f"生成了 {len(phrases)} 个短语组合")
        return phrases

    def _are_related(self, term1: str, term2: str) -> bool:
        """
        简单的相关性判断

        Args:
            term1: 第一个词
            term2: 第二个词

        Returns:
            是否相关
        """
        # 简单实现：检查是否有共同的词
        words1 = set(term1.lower().split())
        words2 = set(term2.lower().split())

        # 如果有共同词，认为相关
        if words1 & words2:
            return True

        # 或者随机认为相关（增加多样性）
        return random.random() < 0.3

    def get_random_term(self) -> str:
        """
        获取随机搜索词（智能选择）

        Returns:
            搜索词
        """
        # 构建候选词池
        candidates = []

        # 40% 概率使用生成的短语
        if self.generated_phrases and random.random() < 0.4:
            candidates.extend(self.generated_phrases)

        # 60% 概率使用基础词
        candidates.extend(self.base_terms)

        # 过滤掉最近使用过的词（避免短期重复）
        available = [t for t in candidates if t not in self.used_terms]

        if not available:
            # 如果所有词都用过了，清空使用记录
            logger.debug("所有搜索词已使用，重置使用记录")
            self.used_terms.clear()
            available = candidates

        # 随机选择
        term = random.choice(available)
        self.used_terms.add(term)

        # 如果使用记录超过候选词的 70%，清空一半
        if len(self.used_terms) > len(candidates) * 0.7:
            old_size = len(self.used_terms)
            self.used_terms = set(list(self.used_terms)[old_size // 2 :])
            logger.debug(f"使用记录过多，清理了 {old_size - len(self.used_terms)} 条")

        logger.debug(f"选择搜索词: {term}")
        return term

    def get_contextual_terms(self, previous_term: str, count: int = 3) -> list[str]:
        """
        获取与前一个搜索词相关的搜索词

        Args:
            previous_term: 前一个搜索词
            count: 返回数量

        Returns:
            相关搜索词列表
        """
        related = []

        # 提取前一个词的关键词
        prev_words = set(previous_term.lower().split())

        # 查找包含相同关键词的搜索词
        for term in self.base_terms + self.generated_phrases:
            if term == previous_term:
                continue

            term_words = set(term.lower().split())

            # 如果有共同词，认为相关
            if prev_words & term_words:
                related.append(term)

        # 如果找不到足够的相关词，随机补充
        while len(related) < count:
            term = random.choice(self.base_terms + self.generated_phrases)
            if term not in related and term != previous_term:
                related.append(term)

        # 随机选择指定数量
        selected = random.sample(related, min(count, len(related)))

        logger.debug(f"为 '{previous_term}' 找到 {len(selected)} 个相关搜索词")
        return selected

    def get_term_statistics(self) -> dict:
        """
        获取搜索词统计信息

        Returns:
            统计信息字典
        """
        return {
            "base_terms_count": len(self.base_terms),
            "generated_phrases_count": len(self.generated_phrases),
            "total_candidates": len(self.base_terms) + len(self.generated_phrases),
            "used_terms_count": len(self.used_terms),
            "available_terms": len(self.base_terms)
            + len(self.generated_phrases)
            - len(self.used_terms),
        }
