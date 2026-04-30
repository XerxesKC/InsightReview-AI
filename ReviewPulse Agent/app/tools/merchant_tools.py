from sqlalchemy import text

async def execute_get_merchant_top_liked_post(session, merchant_id: str) -> str:
    """真实查询数据库的方法"""
    sql = text("""
               SELECT title, content, like_count, create_time
               FROM merchantpost
               WHERE merchant_id = :m_id
                 AND is_deleted = 'F'
               ORDER BY CAST(like_count AS UNSIGNED) DESC LIMIT 1
               """)
    result = await session.execute(sql, {"m_id": str(merchant_id)})
    top_post = result.fetchone()

    if top_post:
        return (
            f"查询到点赞最高的动态：\n"
            f"- 标题：{top_post.title}\n"
            f"- 内容：{top_post.content}\n"
            f"- 点赞数：{top_post.like_count}\n"
            f"- 发布时间：{top_post.create_time}"
        )
    else:
        return "该商家目前没有发布过动态，或者动态没有获得点赞。"


async def execute_get_merchant_latest_comments(session, merchant_id: str, limit: int = 3) -> str:
    """查询商家最新的有效评论"""
    sql = text("""
               SELECT comment_content, rating, env_score, taste_score, service_score, create_time
               FROM comment
               WHERE merchant_id = :m_id
                 AND is_deleted = 'F'
               ORDER BY create_time DESC LIMIT :limit
               """)

    result = await session.execute(sql, {"m_id": str(merchant_id), "limit": limit})
    comments = result.fetchall()

    if not comments:
        return "该商家目前还没有收到任何有效的用户评价。"

    res_text = f"为您查询到该商家的最新 {len(comments)} 条评价：\n"
    for idx, c in enumerate(comments, 1):
        res_text += (
            f"【评价 {idx}】发布时间：{c.create_time}\n"
            f" - 综合评分：{c.rating}分 (环境:{c.env_score} 口味:{c.taste_score} 服务:{c.service_score})\n"
            f" - 评论内容：{c.comment_content}\n"
        )
    return res_text

async def execute_get_merchant_negative_comments(session, merchant_id: str, limit: int = 3) -> str:
    """查询商家近期的差评（评分 < 3.0）"""
    sql = text("""
               SELECT comment_content, rating, env_score, taste_score, service_score, create_time
               FROM comment
               WHERE merchant_id = :m_id
                 AND rating < 3.0
                 AND is_deleted = 'F'
               ORDER BY create_time DESC LIMIT :limit
               """)

    result = await session.execute(sql, {"m_id": str(merchant_id), "limit": limit})
    comments = result.fetchall()

    if not comments:
        return "太棒了！近期您的店铺没有收到低分差评，请继续保持！"

    res_text = f"注意，为您查询到近期有 {len(comments)} 条低分评价：\n"
    for idx, c in enumerate(comments, 1):
        res_text += (
            f"【预警 {idx}】发布时间：{c.create_time}\n"
            f" - 综合评分：{c.rating}分 (环境:{c.env_score} 口味:{c.taste_score} 服务:{c.service_score})\n"
            f" - 顾客吐槽：{c.comment_content}\n"
        )
    res_text += "\n【建议：大模型请针对上述差评内容，为商家生成一段简短的回复话术或整改建议。】"
    return res_text