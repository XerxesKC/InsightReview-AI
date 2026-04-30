package com.example.mybatisplusdemo.web.controller;

import com.example.mybatisplusdemo.common.utls.SessionUtils;
import com.example.mybatisplusdemo.model.domain.User;
import org.springframework.web.bind.annotation.RequestMapping;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import com.example.mybatisplusdemo.common.JsonResponse;
import com.example.mybatisplusdemo.service.IReplyService;
import com.example.mybatisplusdemo.model.domain.Reply;

import java.time.LocalDateTime;
import java.util.List;



@RestController
@RequestMapping("/api/reply")
public class ReplyController {

    private final Logger logger = LoggerFactory.getLogger( ReplyController.class );

    @Autowired
    private IReplyService replyService;


    
    @RequestMapping(value = "/{id}", method = RequestMethod.GET)
    @ResponseBody
    public JsonResponse<Reply> getById(@PathVariable("id") Long id)throws Exception {
        Reply reply = replyService.getById(id);
        return JsonResponse.success(reply);
    }

    
    @PostMapping("/add")
    public JsonResponse<Boolean> add(@RequestBody Reply reply) {
        reply.setIsDeleted("F");
        reply.setCreateTime(LocalDateTime.now());
        reply.setUpdateTime(LocalDateTime.now());
        boolean saved = replyService.save(reply);
        return saved ? JsonResponse.success(true) : JsonResponse.failure("添加失败");
    }

    
    @PutMapping("/update")
    public JsonResponse<Boolean> update(@RequestBody Reply reply) {
        boolean updated = replyService.updateById(reply);
        return updated ? JsonResponse.success(true) : JsonResponse.failure("修改失败");
    }

    
    @DeleteMapping("/delete/{id}")
    public JsonResponse<Boolean> delete(@PathVariable("id") Long id) {
        boolean removed = replyService.removeById(id);
        return removed ? JsonResponse.success(true) : JsonResponse.failure("删除失败");
    }

    
    @PostMapping("/search")
    public JsonResponse<List<Reply>> search(@RequestBody Reply searchParam) {
        String replyId = searchParam.getReplyId();
        String replyContent = searchParam.getReplyContent();
        List<Reply> list = replyService.selectByIdAndContent(replyId, replyContent);
        return JsonResponse.success(list);
    }

    
    @GetMapping("/queryByCommentAndUser")
    public JsonResponse<List<Reply>> queryByCommentAndUser(
            @RequestParam("commentId") String commentId,
            @RequestParam("replyTo") String replyTo
    ) {
        List<Reply> replies = replyService.getRepliesByCommentIdAndReplyTo(commentId, replyTo);
        return JsonResponse.success(replies);
    }

    @GetMapping("/getReplies")
    public JsonResponse getReplies() {
        List<Reply> list = replyService.getReplies();
        return JsonResponse.success(list);
    }
}
