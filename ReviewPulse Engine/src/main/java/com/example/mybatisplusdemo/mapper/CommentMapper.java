package com.example.mybatisplusdemo.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.mybatisplusdemo.model.domain.Comment;
import org.apache.ibatis.annotations.Param;

import java.util.List;


public interface CommentMapper extends BaseMapper<Comment> {
    List<Comment> selectByIdAndContent(@Param("commentId") String commentId, @Param("commentContent") String commentContent);

    List<Comment> getMerchantPostComments(@Param("merchantId") String merchantId);

    List<Comment> getMerchantComments(@Param("merchantId") String merchantId);

    IPage<Comment> selectByMerchantIdWithPage(@Param("merchantId") String merchantId, Page<Comment> page);
    IPage<Comment> selectByMerchantIdAndPostId(@Param("merchantId") String merchantId,@Param("postId") String postId, Page<Comment> page);
    List<Comment> getComments();


    Integer updateStatus(@Param("comment") Comment comment);

    Integer deleteMy(@Param("comment") Comment comment);
}
