
from datetime import datetime, timezone
from supabase import Client


def get_task_progress(supabase: Client, task_id: int):
    """指定した課題の達成状況を取得する。"""

    result = (
        supabase.table("task_progress")
        .select(
            "task_id, player_id, is_achieved, "
            "clear_type, ex_score, dj_level, updated_at"
        )
        .eq("task_id", task_id)
        .execute()
    )

    return result.data


def mark_task_achieved(
    supabase: Client,
    task_id: int,
    player_id: int,
):
    """課題を達成済みにする。"""

    result = (
        supabase.table("task_progress")
        .upsert(
            {
                "task_id": task_id,
                "player_id": player_id,
                "is_achieved": True,
                "updated_at": datetime.now(
                    timezone.utc
                ).isoformat(),
            },
            on_conflict="task_id,player_id",
        )
        .execute()
    )

    return result.data


def mark_task_unachieved(
    supabase: Client,
    task_id: int,
    player_id: int,
):
    """課題を未達成に戻す。"""

    result = (
        supabase.table("task_progress")
        .upsert(
            {
                "task_id": task_id,
                "player_id": player_id,
                "is_achieved": False,
                "updated_at": datetime.now(
                    timezone.utc
                ).isoformat(),
            },
            on_conflict="task_id,player_id",
        )
        .execute()
    )

    return result.data
