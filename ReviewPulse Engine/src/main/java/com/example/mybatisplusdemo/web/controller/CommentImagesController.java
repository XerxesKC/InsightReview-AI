package com.example.mybatisplusdemo.web.controller;

import org.springframework.web.bind.annotation.RequestMapping;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import com.example.mybatisplusdemo.common.JsonResponse;
import com.example.mybatisplusdemo.service.ICommentImagesService;
import com.example.mybatisplusdemo.model.domain.CommentImages;
import com.example.mybatisplusdemo.model.dto.CommentImagesDTO;



@RestController
@RequestMapping("/api/commentImages")
public class CommentImagesController {

    private final Logger logger = LoggerFactory.getLogger( CommentImagesController.class );

    @Autowired
    private ICommentImagesService commentImagesService;


    
    @RequestMapping(value = "/{id}", method = RequestMethod.GET)
    @ResponseBody
    public JsonResponse<CommentImages> getById(@PathVariable("id") Long id)throws Exception {
        CommentImages commentImages = commentImagesService.getById(id);
        return JsonResponse.success(commentImages);
    }

    
    @PostMapping("/add")
    public JsonResponse<Boolean> add(@RequestBody CommentImagesDTO dto) {
        CommentImages commentImages = new CommentImages();
        org.springframework.beans.BeanUtils.copyProperties(dto, commentImages);
        boolean saved = commentImagesService.save(commentImages);
        return saved ? JsonResponse.success(true) : JsonResponse.failure("添加失败");
    }

    
    @PostMapping("/update")
    public JsonResponse<Boolean> update(@RequestBody CommentImagesDTO dto) {
        CommentImages commentImages = new CommentImages();
        org.springframework.beans.BeanUtils.copyProperties(dto, commentImages);
        boolean updated = commentImagesService.updateById(commentImages);
        return updated ? JsonResponse.success(true) : JsonResponse.failure("修改失败");
    }

    
    @PostMapping("/delete/{id}")
    public JsonResponse<Boolean> delete(@PathVariable("id") Long id) {
        boolean removed = commentImagesService.removeById(id);
        return removed ? JsonResponse.success(true) : JsonResponse.failure("删除失败");
    }
}
