from sqlalchemy import text


async def execute_get_user_latest_comments(session, user_id: str, limit: int = 3) -> str:
    """查询普通用户最新发布的评论"""
    sql = text("""
               SELECT comment_content, rating, env_score, taste_score, service_score, create_time
               FROM comment
               WHERE user_id = :u_id
                 AND is_deleted = 'F'
               ORDER BY create_time DESC LIMIT :limit
               """)

    result = await session.execute(sql, {"u_id": str(user_id), "limit": limit})
    comments = result.fetchall()

    if not comments:
        return "您目前还没有发布过任何有效的评价记录。"

    res_text = f"为您查询到您最新发布的 {len(comments)} 条评价：\n"
    for idx, c in enumerate(comments, 1):
        res_text += (
            f"【评价 {idx}】发布时间：{c.create_time}\n"
            f" - 综合评分：{c.rating}分 (环境:{c.env_score} 口味:{c.taste_score} 服务:{c.service_score})\n"
            f" - 评论内容：{c.comment_content}\n"
        )
    return res_text


async def execute_summarize_merchant_comments(session, merchant_name: str) -> str:
    """根据商家名称查询近期评价，供大模型总结"""

    sql = text("""
               SELECT c.comment_content, c.rating, c.env_score, c.taste_score, c.service_score
               FROM comment c
                        JOIN merchant m ON c.merchant_id = m.merchant_id
               WHERE m.merchant_name LIKE :m_name
                 AND c.is_deleted = 'F'
               ORDER BY c.create_time DESC LIMIT 20
               """)

    result = await session.execute(sql, {"m_name": f"%{merchant_name}%"})
    comments = result.fetchall()

    if not comments:
        return f"系统未查询到名为【{merchant_name}】的店铺，或者该店铺目前还没有任何有效的用户评价。"

    res_text = f"为您查询到【{merchant_name}】的最新 {len(comments)} 条评价数据：\n"
    for idx, c in enumerate(comments, 1):
        res_text += (
            f"【评价{idx}】 综合:{c.rating}分 (环境{c.env_score} 口味{c.taste_score} 服务{c.service_score}) "
            f"内容：{c.comment_content}\n"
        )

    res_text += "\n【系统提示：请根据以上真实的评价数据，为用户写一段条理清晰、自然亲切的店铺口碑总结（可以分综合评分、口味、环境、服务等维度）。】"

    return res_text


async def execute_search_merchants(session, keyword: str = "", min_rating: float = 0.0,
                                   max_price: float = 9999.0) -> str:
    """根据条件搜索商家"""
    sql = text("""
               SELECT merchant_name, tag, description, address, contact_phone
               FROM merchant
               WHERE (merchant_name LIKE :kw OR tag LIKE :kw OR description LIKE :kw)
                     AND avg_rating >= :min_rating 
                     AND price_level <= :max_price
                   LIMIT 5
               """)

    result = await session.execute(sql, {"kw": f"%{keyword}%", "min_rating": min_rating, "max_price": max_price})
    merchants = result.fetchall()

    if not merchants:
        return "很抱歉，没有找到完全符合您条件的商家，您可以换个关键词试试。"

    res_text = f"为您找到以下符合条件的优质商家：\n"
    for idx, m in enumerate(merchants, 1):
        res_text += (
            f"{idx}. 【{m.merchant_name}】\n"
            f"   - 推荐理由：{m.description}\n"
            f"   - 商家标签：{m.tag}\n"
            f"   - 联系电话：{m.contact_phone}\n"
            f"   - 店铺地址：{m.address}\n\n"
        )
    return res_text


async def execute_get_user_bookmarks(session, user_id: str) -> str:
    """查询用户收藏的商家"""
    sql = text("""
               SELECT m.merchant_name, m.tag as merchant_tag, m.address, f.tag as user_remark, f.create_time
               FROM favorite f
               JOIN merchant m ON f.merchant_id = m.merchant_id
               WHERE f.user_id = :u_id AND f.is_deleted = 'F'
               ORDER BY f.create_time DESC LIMIT 10
               """)
    result = await session.execute(sql, {"u_id": str(user_id)})
    bookmarks = result.fetchall()

    if not bookmarks:
        return "您目前还没有收藏任何店铺哦，快去小众点评探索一下吧！"

    res_text = "这是您收藏的店铺列表：\n"
    for idx, row in enumerate(bookmarks, 1):
        remark_info = f" (您的备注: {row.user_remark})" if row.user_remark and row.user_remark != '默认' else ""

        res_text += (
            f"{idx}. 【{row.merchant_name}】{remark_info}\n"
            f"   - 标签：{row.merchant_tag}\n"
            f"   - 地址：{row.address}\n"
        )

    res_text += "\n【系统提示：请根据上述列表，用亲切的语气为用户总结其收藏夹内容。】"
    return res_text
