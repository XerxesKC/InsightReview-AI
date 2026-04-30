package com.example.mybatisplusdemo.web.controller;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.mybatisplusdemo.model.domain.Comment;
import com.example.mybatisplusdemo.model.domain.User;
import org.springframework.web.bind.annotation.RequestMapping;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import com.example.mybatisplusdemo.common.JsonResponse;
import com.example.mybatisplusdemo.service.IMerchantpostService;
import com.example.mybatisplusdemo.model.domain.Merchantpost;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;



@RestController
@RequestMapping("/api/merchantpost")
public class MerchantpostController {

    private final Logger logger = LoggerFactory.getLogger( MerchantpostController.class );

    @Autowired
    private IMerchantpostService merchantpostService;

    
    @RequestMapping(value = "/{id}", method = RequestMethod.GET)
    @ResponseBody
    public JsonResponse<Merchantpost> getById(@PathVariable("id") Long id)throws Exception {
        Merchantpost merchantpost = merchantpostService.getById(id);
        return JsonResponse.success(merchantpost);
    }

    @PostMapping("postDelete")
    public JsonResponse postDelete(@RequestBody Map<String, Integer> req) {
        boolean b = merchantpostService.removeById(req.get("id"));
        return JsonResponse.success(b);
    }

    @PostMapping("postInsert")
    public JsonResponse postInsert(@RequestBody Merchantpost merchantpost){
        merchantpost.setCreateTime(LocalDateTime.now());
        merchantpost.setUpdateTime(LocalDateTime.now());
        merchantpost.setIsDeleted("F");
        boolean b = merchantpostService.save(merchantpost);
        return JsonResponse.success(b);
    }

    @PostMapping("postUpdate")
    public JsonResponse postUpdate(@RequestBody Merchantpost merchantpost) {
        if (merchantpost.getPostId() == null) {
            return JsonResponse.failure("更新失败：必须提供postId");
        }

        merchantpost.setUpdateTime(LocalDateTime.now());

        boolean isUpdated = merchantpostService.updateById(merchantpost);

        return isUpdated ?
                JsonResponse.successMessage("更新成功") :
                JsonResponse.failure("更新失败：记录不存在或数据未变化");
    }

    @GetMapping("getContents")
    public JsonResponse getContents(String merchantId) {
        List<Merchantpost> list = merchantpostService.getContents(merchantId);
        return JsonResponse.success(list);
    }

    @PostMapping("deleteContent")
    public JsonResponse deleteContent(@RequestBody Merchantpost merchantpost) {
        boolean b = merchantpostService.removeById(merchantpost.getPostId());
        return JsonResponse.success(b);
    }

    @PostMapping("addLikeCount")
    public JsonResponse<Merchantpost> updateMy(@RequestBody Merchantpost merchantpost)throws Exception{
        merchantpostService.addLikeCount(merchantpost);
        return JsonResponse.success(merchantpostService.getById(merchantpost));
    }

}

