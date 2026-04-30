package com.example.mybatisplusdemo.service;

import com.example.mybatisplusdemo.model.domain.Reply;
import com.baomidou.mybatisplus.extension.service.IService;

import java.util.List;


public interface IReplyService extends IService<Reply> {
    List<Reply> selectByIdAndContent(String replyId, String replyContent);

    
    List<Reply> getRepliesByCommentIdAndReplyTo(String commentId, String replyTo);

    List<Reply> getReplies();
}
