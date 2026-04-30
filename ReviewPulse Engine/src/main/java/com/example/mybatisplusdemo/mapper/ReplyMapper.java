package com.example.mybatisplusdemo.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.mybatisplusdemo.model.domain.Reply;
import org.apache.ibatis.annotations.Param;

import java.util.List;


public interface ReplyMapper extends BaseMapper<Reply> {
    List<Reply> selectByIdAndContent(@Param("replyId") String replyId, @Param("replyContent") String replyContent);

    List<Reply> getReplies();

    List<Reply> getRepliesByCommentIdAndReplyTo(String commentId, String replyTo);
}
