package com.example.mybatisplusdemo.web.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.mybatisplusdemo.model.domain.Merchant;
import com.example.mybatisplusdemo.model.domain.Merchantpost;
import com.example.mybatisplusdemo.service.ICommentService;
import org.springframework.web.bind.annotation.RequestMapping;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import com.example.mybatisplusdemo.common.JsonResponse;
import com.example.mybatisplusdemo.model.domain.Comment;

import com.example.mybatisplusdemo.common.utls.SessionUtils;
import com.example.mybatisplusdemo.model.domain.User;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;



@RestController
@RequestMapping("/api/comment")
public class CommentController {

    private final Logger logger = LoggerFactory.getLogger( CommentController.class );

    @Autowired
    private ICommentService commentService;

    
    @PostMapping("/add")
    public JsonResponse<Boolean> add(@RequestBody Comment comment) {
        comment.setIsAnonymous("N");
        comment.setIsDeleted("F");
        comment.setCreateTime(LocalDateTime.now());
        comment.setUpdateTime(LocalDateTime.now());
        comment.setStatus("G");
        boolean saved = commentService.save(comment);
        return saved ? JsonResponse.success(true) : JsonResponse.failure("添加失败");
    }

    
    @PostMapping("/update")
    public JsonResponse<Boolean> update(@RequestBody Comment comment) {
        if (comment.getCommentId() == null) {
            return JsonResponse.failure("评论 ID 不能为空");
        }

        Comment existing = commentService.getById(comment.getCommentId());
        if (existing == null || !"F".equals(existing.getIsDeleted())) {
            return JsonResponse.failure("该评论不存在或已被删除");
        }

        boolean updated = commentService.updateById(comment);
        return updated ? JsonResponse.success(true) : JsonResponse.failure("修改失败");
    }

    
    @PostMapping("/delete")
    public JsonResponse<Boolean> deleteComment(@RequestBody Map<String, String> request) {
        String id = request.get("commentId");
        if (id == null || id.trim().isEmpty()) {
            return JsonResponse.failure("评论 ID 不能为空");
        }

        Comment comment = new Comment();
        comment.setCommentId(id);
        comment.setIsDeleted("T");

        boolean updated = commentService.updateById(comment);
        return updated ? JsonResponse.success(true) : JsonResponse.failure("删除失败");
    }

    
    @PostMapping("/userDelete")
    public JsonResponse<Boolean> userDeleteComment(@RequestBody Map<String, String> request) {
        String id = request.get("commentId");
        if (id == null || id.trim().isEmpty()) {
            return JsonResponse.failure("评论 ID 不能为空");
        }

        User currentUser = SessionUtils.getCurrentUserInfo();
        if (currentUser == null) {
            return JsonResponse.failure("用户未登录");
        }

        Comment comment = commentService.getById(id);
        if (comment == null) {
            return JsonResponse.failure("评论不存在");
        }

        if (!comment.getUserId().equals(currentUser.getUserId()) || !"F".equals(comment.getIsDeleted())) {
            return JsonResponse.failure("不能删除别人的评论或已删除的评论");
        }

        comment.setIsDeleted("T");

        boolean updated = commentService.updateById(comment);
        return updated ? JsonResponse.success(true) : JsonResponse.failure("删除失败");
    }

    
    @PostMapping("/search")
    public JsonResponse<List<Comment>> search(@RequestBody Comment searchParam) {
        String commentId = searchParam.getCommentId() == null ? null : searchParam.getCommentId().toString();
        String commentContent = searchParam.getCommentContent();
        List<Comment> list = commentService.selectByIdAndContent(commentId, commentContent);
        return JsonResponse.success(list);
    }

    
    @GetMapping("/selectByMerchantId")
    public JsonResponse<IPage<Comment>> getByMerchantIdWithPage(
            @RequestParam("merchantId") String merchantId,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size
    ) {
        Page<Comment> pageRequest = new Page<>(page, size);
        IPage<Comment> commentPage = commentService.selectByMerchantIdWithPage(merchantId, pageRequest);
        return JsonResponse.success(commentPage);
    }

    
    @GetMapping("/selectByMerchantIdAndPostId")
    public JsonResponse<IPage<Comment>> selectByMerchantIdAndPostId(
            @RequestParam("merchantId") String merchantId,
            @RequestParam("postId") String postId,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size
    ) {
        Page<Comment> pageRequest = new Page<>(page, size);
        IPage<Comment> commentPage = commentService.selectByMerchantIdAndPostId(merchantId,postId,pageRequest);
        return JsonResponse.success(commentPage);
    }

    @GetMapping("getMerchantPostComments")
    public JsonResponse getMerchantPostComments(String merchantId) {
        List<Comment> list = commentService.getMerchantPostComments(merchantId);
        return JsonResponse.success(list);
    }

    @GetMapping("getMerchantComments")
    public JsonResponse getMerchantComments(String merchantId) {
        List<Comment> list = commentService.getMerchantComments(merchantId);
        return JsonResponse.success(list);
    }

    @GetMapping("getComments")
    public JsonResponse getComments() {
        List<Comment> list = commentService.getComments();
        return JsonResponse.success(list);
    }

    @PostMapping("deleteComment")
    public JsonResponse deleteComment(@RequestBody Comment comment) {
        commentService.deleteMy(comment);
        return JsonResponse.success(commentService.getById(comment));
    }

    @PostMapping("changeCommentStatus")
    public JsonResponse<Comment> updateMy(@RequestBody Comment comment)throws Exception{
        commentService.updateStatus(comment);
        return JsonResponse.success(commentService.getById(comment));
    }

    @GetMapping("/getCommentsByUserId")
    public JsonResponse<IPage<Comment>> getCommentsByUserId(
            @RequestParam("userId") String userId,
            @RequestParam(value = "pageNum", defaultValue = "1") int pageNum,
            @RequestParam(value = "pageSize", defaultValue = "10") int pageSize
    ) {
        Page<Comment> page = new Page<>(pageNum, pageSize);
        IPage<Comment> commentPage = commentService.getPageCommentsByUserId(page, userId);
        return JsonResponse.success(commentPage);
    }
}
