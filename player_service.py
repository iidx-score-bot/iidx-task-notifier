
from supabase import Client


def register_player(
    supabase: Client,
    line_user_id: str,
    display_name: str | None = None,
):
    """LINEユーザーを登録し、プレイヤー情報を返す。"""

    if not line_user_id:
        raise ValueError("LINEユーザーIDがありません")

    result = (
        supabase.table("players")
        .upsert(
            {
                "line_user_id": line_user_id,
                "display_name": display_name,
            },
            on_conflict="line_user_id",
        )
        .execute()
    )

    return result.data[0]


def get_player(supabase: Client, line_user_id: str):
    """LINEユーザーIDからプレイヤーを取得する。"""

    if not line_user_id:
        return None

    result = (
        supabase.table("players")
        .select("id, line_user_id, display_name")
        .eq("line_user_id", line_user_id)
        .limit(1)
        .execute()
    )

    return result.data[0] if result.data else None
