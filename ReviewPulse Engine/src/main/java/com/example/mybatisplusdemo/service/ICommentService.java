package com.example.mybatisplusdemo.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.mybatisplusdemo.model.domain.Comment;
import com.baomidou.mybatisplus.extension.service.IService;
import com.example.mybatisplusdemo.model.domain.Merchantpost;

import java.util.List;


public interface ICommentService extends IService<Comment> {
    List<Comment> selectByIdAndContent(String commentId, String commentContent);

    IPage<Comment> selectByMerchantIdWithPage(String merchantId, Page<Comment> page);

    IPage<Comment> selectByMerchantIdAndPostId(String merchantId,String postId, Page<Comment> page);
    List<Comment> getMerchantPostComments(String merchantId);

    List<Comment> getMerchantComments(String merchantId);

    List<Comment> getComments();

    Integer updateStatus(Comment comment);

    Integer deleteMy(Comment comment);
    IPage<Comment> getPageCommentsByUserId(Page<Comment> page, String userId);
}
