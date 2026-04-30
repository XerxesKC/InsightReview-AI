package com.example.mybatisplusdemo.web.controller;

import org.springframework.web.bind.annotation.RequestMapping;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import com.example.mybatisplusdemo.common.JsonResponse;
import com.example.mybatisplusdemo.service.ICommentVideosService;
import com.example.mybatisplusdemo.model.domain.CommentVideos;
import com.example.mybatisplusdemo.model.dto.CommentVideosDTO;



@RestController
@RequestMapping("/api/commentVideos")
public class CommentVideosController {

    private final Logger logger = LoggerFactory.getLogger( CommentVideosController.class );

    @Autowired
    private ICommentVideosService commentVideosService;


    
    @RequestMapping(value = "/{id}", method = RequestMethod.GET)
    @ResponseBody
    public JsonResponse<CommentVideos> getById(@PathVariable("id") Long id)throws Exception {
        CommentVideos commentVideos = commentVideosService.getById(id);
        return JsonResponse.success(commentVideos);
    }

    
    @PostMapping("/add")
    public JsonResponse<Boolean> add(@RequestBody CommentVideosDTO dto) {
        CommentVideos commentVideos = new CommentVideos();
        org.springframework.beans.BeanUtils.copyProperties(dto, commentVideos);
        boolean saved = commentVideosService.save(commentVideos);
        return saved ? JsonResponse.success(true) : JsonResponse.failure("添加失败");
    }

    
    @PostMapping("/update")
    public JsonResponse<Boolean> update(@RequestBody CommentVideosDTO dto) {
        CommentVideos commentVideos = new CommentVideos();
        org.springframework.beans.BeanUtils.copyProperties(dto, commentVideos);
        boolean updated = commentVideosService.updateById(commentVideos);
        return updated ? JsonResponse.success(true) : JsonResponse.failure("修改失败");
    }

    
    @PostMapping("/delete/{id}")
    public JsonResponse<Boolean> delete(@PathVariable("id") Long id) {
        boolean removed = commentVideosService.removeById(id);
        return removed ? JsonResponse.success(true) : JsonResponse.failure("删除失败");
    }
}
