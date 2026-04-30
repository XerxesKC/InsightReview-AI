package com.example.mybatisplusdemo.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.mybatisplusdemo.model.domain.Comment;
import com.example.mybatisplusdemo.mapper.CommentMapper;
import com.example.mybatisplusdemo.model.domain.Merchant;
import com.example.mybatisplusdemo.model.domain.Merchantpost;
import com.example.mybatisplusdemo.service.ICommentService;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import org.springframework.stereotype.Service;
import org.springframework.beans.factory.annotation.Autowired;

import java.util.ArrayList;
import java.util.List;


@Service
public class CommentServiceImpl extends ServiceImpl<CommentMapper, Comment> implements ICommentService {

    @Autowired
    private CommentMapper commentMapper;

    @Override
    public List<Comment> selectByIdAndContent(String commentId, String commentContent) {
        return commentMapper.selectByIdAndContent(commentId, commentContent);
    }

    @Override
    public IPage<Comment> selectByMerchantIdWithPage(String merchantId, Page<Comment> page) {
        return commentMapper.selectByMerchantIdWithPage(merchantId, page);
    }

    @Override
    public IPage<Comment> selectByMerchantIdAndPostId(String merchantId,String postId, Page<Comment> page) {
        return commentMapper.selectByMerchantIdAndPostId(merchantId,postId,page);
    }

    @Override
    public List<Comment> getMerchantPostComments(String merchantId) {
        List<Comment> list = new ArrayList<>();
        list = commentMapper.getMerchantPostComments(merchantId);
        return list;
    }

    @Override
    public List<Comment> getMerchantComments(String merchantId) {
        List<Comment> list = new ArrayList<>();
        list = commentMapper.getMerchantComments(merchantId);
        return list;
    }

    @Override
    public List<Comment> getComments() {
        List<Comment> list = new ArrayList<>();
        list = commentMapper.getComments();
        return list;
    }

    @Override
    public IPage<Comment> getPageCommentsByUserId(Page<Comment> page, String userId) {
        LambdaQueryWrapper<Comment> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(Comment::getUserId, userId).eq(Comment::getIsDeleted, "F");
        wrapper.orderByDesc(Comment::getCreateTime);
        return commentMapper.selectPage(page, wrapper);
    }

    @Override
    public Integer updateStatus(Comment comment) {
        return commentMapper.updateStatus(comment);
    }

    @Override
    public Integer deleteMy(Comment comment) {
        return commentMapper.deleteMy(comment);
    }

}
