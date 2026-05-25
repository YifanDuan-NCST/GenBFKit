# -*- coding: utf-8 -*-
"""
Mock Data API Routes - 虚拟数据生成相关的 API 路由
"""

from typing import Optional

from fastapi import APIRouter, Query, BackgroundTasks
from fastapi.responses import JSONResponse

import asyncio
import threading
from datetime import datetime

from ..services.database_manager import get_manager
from ..mock_data.generator import MockDataGenerator


router = APIRouter()

# 全局生成器状态
_generation_status = {
    "running": False,
    "progress": 0,
    "total": 0,
    "current_table": "",
    "start_time": None,
    "last_stats": None,
    "result": None,
}
_lock = threading.Lock()


def _run_generation_sync(
    rows: int,
    mode: str,
    seed: Optional[int],
    batch_size: int,
    max_tables: Optional[int],
):
    """在后台线程中运行数据生成（同步方式，避免阻塞事件循环）"""
    global _generation_status

    with _lock:
        _generation_status["running"] = True
        _generation_status["progress"] = 0
        _generation_status["start_time"] = datetime.now()
        _generation_status["result"] = None

    def progress_callback(table_name: str, idx: int, total: int):
        with _lock:
            _generation_status["progress"] = idx
            _generation_status["total"] = total
            _generation_status["current_table"] = table_name

    try:
        generator = MockDataGenerator(
            rows_per_table=rows,
            seed=seed,
        )
        stats = generator.generate_all(
            mode=mode,
            batch_size=batch_size,
            max_tables=max_tables,
            progress_callback=progress_callback,
        )
        with _lock:
            _generation_status["result"] = stats.to_dict()
    except Exception as e:
        with _lock:
            _generation_status["result"] = {"error": str(e)}
    finally:
        with _lock:
            _generation_status["running"] = False
            _generation_status["progress"] = _generation_status["total"]


@router.get("/mock/status")
async def get_generation_status():
    """获取虚拟数据生成状态"""
    with _lock:
        status = dict(_generation_status)
    elapsed = None
    if status["start_time"]:
        elapsed = (datetime.now() - status["start_time"]).total_seconds()
    return {
        "running": status["running"],
        "progress": status["progress"],
        "total": status["total"],
        "current_table": status["current_table"],
        "elapsed_seconds": round(elapsed, 1) if elapsed else 0,
        "percentage": (
            round(status["progress"] / status["total"] * 100, 1)
            if status["total"] > 0 else 0
        ),
        "result": status["result"],
    }


@router.post("/mock/generate-all")
async def generate_all_mock_data(
    background_tasks: BackgroundTasks,
    rows: int = Query(100, ge=1, le=10000, description="每个表生成的行数"),
    mode: str = Query("upsert", description="upsert=已满跳过, overwrite=先清空再插入"),
    seed: Optional[int] = Query(None, description="随机数种子，用于可复现数据"),
    batch_size: int = Query(500, ge=10, le=5000, description="每批插入行数"),
    max_tables: Optional[int] = Query(None, ge=1, description="最大处理表数"),
):
    """
    为所有物理表生成虚拟数据（后台执行）

    - **rows**: 每个物理表生成的行数（默认100）
    - **mode**: upsert（已满则跳过）或 overwrite（先清空再插入）
    - **seed**: 随机数种子（固定则每次生成相同数据）
    - **batch_size**: 批量插入大小
    - **max_tables**: 最大处理表数（用于测试）
    """
    global _generation_status

    with _lock:
        if _generation_status["running"]:
            return JSONResponse(
                status_code=409,
                content={
                    "success": False,
                    "message": "生成任务已在运行中，请等待完成",
                    "status": "running",
                },
            )

    # 在后台线程中执行（避免阻塞 FastAPI 事件循环）
    thread = threading.Thread(
        target=_run_generation_sync,
        args=(rows, mode, seed, batch_size, max_tables),
        daemon=True,
    )
    thread.start()

    return {
        "success": True,
        "message": f"数据生成任务已启动，正在为所有物理表生成 {rows} 行数据...",
        "status": "started",
    }


@router.post("/mock/generate")
async def generate_single_table(
    table_name: str = Query(..., description="物理表名"),
    rows: int = Query(100, ge=1, le=10000, description="生成的行数"),
    mode: str = Query("upsert", description="upsert 或 overwrite"),
    seed: Optional[int] = Query(None, description="随机数种子"),
):
    """
    为单个物理表生成虚拟数据
    """
    try:
        generator = MockDataGenerator(rows_per_table=rows, seed=seed)
        result = generator.generate_for_table(table_name, mode=mode)

        if result["success"]:
            return {
                "success": True,
                "table_name": table_name,
                "rows_inserted": result["rows_inserted"],
                "message": f"成功为表 {table_name} 生成 {result['rows_inserted']} 行数据",
            }
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "table_name": table_name,
                    "error": result["error"],
                },
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)},
        )


@router.get("/mock/preview/{table_name}")
async def preview_table_data(
    table_name: str,
    limit: int = Query(5, ge=1, le=100, description="预览行数"),
):
    """
    预览物理表中的数据（前 N 行）

    用于前端在弹窗中展示表内实际数据，而不仅仅是表结构。
    """
    try:
        generator = MockDataGenerator()
        preview = generator.preview_table_data(table_name, limit=limit)

        if "error" in preview:
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": preview["error"]},
            )

        return {
            "success": True,
            "table_name": table_name,
            "columns": preview["columns"],
            "column_types": preview["column_types"],
            "rows": preview["rows"],
            "total_rows": preview["total_rows"],
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)},
        )
