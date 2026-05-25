"""
Chain Retriever - Implements the five-level chain-like retrieval logic.

Provides structured retrieval methods that follow the dictionary hierarchy:
    work type → data category → data pool → dataset → data attribute

Supports multi-level filtering and intersection queries.
"""

import logging
from typing import Optional
from .dictionary_manager import (
    DictionaryManager,
    Dataset,
    DataCategory,
    DataPool,
    WorkType,
    AttributeTemplate,
)

logger = logging.getLogger(__name__)


class RetrievalResult:
    """
    Encapsulates a single retrieval result with full chain context.

    Each result carries the complete lineage from work type down to attributes,
    enabling users to understand where each parameter sits in the hierarchy.
    """

    def __init__(
        self,
        dataset: Dataset,
        work_type: Optional[WorkType] = None,
        category: Optional[DataCategory] = None,
        pool: Optional[DataPool] = None,
        attributes: Optional[AttributeTemplate] = None,
        relevance_score: float = 0.0,
    ):
        self.dataset = dataset
        self.work_type = work_type
        self.category = category
        self.pool = pool
        self.attributes = attributes
        self.relevance_score = relevance_score

    def to_dict(self) -> dict:
        return {
            "parameter": {
                "en": self.dataset.dataset_en,
                "zh": self.dataset.dataset_zh,
                "zh_short": self.dataset.dataset_zh_short,
            },
            "work_type": {
                "en": self.work_type.work_type_en if self.work_type else self.dataset.work_type_en,
                "zh": self.work_type.work_type_zh if self.work_type else "",
            },
            "category": {
                "en": self.category.category_en if self.category else self.dataset.category_en,
                "zh": self.category.category_zh if self.category else "",
            },
            "data_pool": {
                "en": self.pool.pool_en if self.pool else self.dataset.pool_en,
                "zh": self.pool.pool_zh if self.pool else "",
            },
            "attributes": self.attributes.model_dump() if self.attributes else None,
            "relevance_score": round(self.relevance_score, 4),
        }


class ChainRetriever:
    """
    Chain Retriever - The workhorse for hierarchical data retrieval.

    Implements the core "Task Requirement → Hierarchical Retrieval → Parameter Location"
    logic by leveraging the Dictionary Manager's chain-like architecture.

    Key design:
      - Level-by-level filtering with early termination
      - Support for multiple filter conditions (intersection semantics)
      - Automatic attribute resolution based on pool association
      - Results enriched with full chain context
    """

    def __init__(self, dict_manager: DictionaryManager):
        self._dm = dict_manager

    def retrieve(
        self,
        work_types: Optional[list[str]] = None,
        categories: Optional[list[str]] = None,
        pools: Optional[list[str]] = None,
        keyword: Optional[str] = None,
        keyword_field: str = "both",
    ) -> list[RetrievalResult]:
        """
        Execute chain-like retrieval with multi-level filters.

        Args:
            work_types:  Filter by work type English names (Level 1)
            categories:  Filter by category English names (Level 2)
            pools:       Filter by pool English names (Level 3)
            keyword:     Free-text keyword to match against parameter names (Level 4)
            keyword_field: "en", "zh", or "both" for keyword matching scope

        Returns:
            List of RetrievalResult objects with full chain context
        """
        # Start from the full dataset
        candidates = self._dm.get_all_datasets()

        # Level 1: Work type filter
        if work_types:
            candidates = [d for d in candidates if d.work_type_en in work_types]
            logger.debug(f"After work_type filter: {len(candidates)} candidates")

        # Level 2: Category filter
        if categories:
            candidates = [d for d in candidates if d.category_en in categories]
            logger.debug(f"After category filter: {len(candidates)} candidates")

        # Level 3: Pool filter
        if pools:
            candidates = [d for d in candidates if d.pool_en in pools]
            logger.debug(f"After pool filter: {len(candidates)} candidates")

        # Level 4: Keyword matching
        if keyword:
            kw_lower = keyword.lower()
            filtered = []
            for d in candidates:
                match = False
                if keyword_field in ("en", "both"):
                    match = match or kw_lower in d.dataset_en.lower()
                if keyword_field in ("zh", "both"):
                    match = match or kw_lower in d.dataset_zh.lower()
                if match:
                    filtered.append(d)
            candidates = filtered
            logger.debug(f"After keyword filter: {len(candidates)} candidates")

        # Enrich with chain context and resolve attributes (Level 5)
        results = []
        for ds in candidates:
            wt = self._dm._wt_index.get(ds.work_type_en)
            # Find matching category
            cat = None
            for c in self._dm.get_categories_by_work_type(ds.work_type_en):
                if c.category_en == ds.category_en:
                    cat = c
                    break
            pool = self._dm.get_pool(ds.pool_en)
            attrs = self._dm.get_attributes_by_pool(ds.pool_en)

            results.append(RetrievalResult(
                dataset=ds,
                work_type=wt,
                category=cat,
                pool=pool,
                attributes=attrs,
            ))

        logger.info(f"Chain retrieval returned {len(results)} results")
        return results

    def retrieve_by_task(
        self,
        task_config: dict,
    ) -> list[RetrievalResult]:
        """
        Task-oriented retrieval: accepts a structured task configuration
        and returns fully contextualized results.

        Task config format:
        {
            "work_types": ["BF operating", ...],     # optional
            "categories": ["..."],                    # optional
            "pools": ["Continuous time-series data"], # optional
            "keywords": ["temperature", "pressure"], # optional, OR semantics
            "keyword_field": "both"                   # optional
        }

        Retrieval strategy:
          - work_types is a mandatory filter (AND with everything else)
          - categories and pools use OR semantics: results matching EITHER
            the category filter OR the pool filter are included
          - keywords use OR semantics across keyword terms
        """
        work_types = task_config.get("work_types")
        categories = task_config.get("categories")
        pools = task_config.get("pools")
        keywords = task_config.get("keywords", [])
        keyword_field = task_config.get("keyword_field", "both")

        # Strategy: when both categories and pools are specified,
        # use OR semantics to avoid empty intersections
        if categories and pools:
            # Query with category filter (within work_type scope)
            cat_results = self.retrieve(
                work_types=work_types,
                categories=categories,
                keyword_field=keyword_field,
            )
            # Query with pool filter (within work_type scope)
            pool_results = self.retrieve(
                work_types=work_types,
                pools=pools,
                keyword_field=keyword_field,
            )
            # Merge with deduplication
            seen = {r.dataset.dataset_en for r in cat_results}
            results = list(cat_results)
            for r in pool_results:
                if r.dataset.dataset_en not in seen:
                    results.append(r)
                    seen.add(r.dataset.dataset_en)
        else:
            # Simple case: only one of categories or pools (or neither)
            results = self.retrieve(
                work_types=work_types,
                categories=categories,
                pools=pools,
                keyword_field=keyword_field,
            )

        # If keywords provided, apply OR-based keyword matching
        if keywords:
            kw_results = []
            for kw in keywords:
                kw_results.extend(self.retrieve(
                    work_types=work_types,
                    categories=categories,
                    pools=pools,
                    keyword=kw,
                    keyword_field=keyword_field,
                ))
            # Merge and deduplicate by dataset_en
            seen = {r.dataset.dataset_en for r in results}
            for r in kw_results:
                if r.dataset.dataset_en not in seen:
                    results.append(r)
                    seen.add(r.dataset.dataset_en)

        return results
