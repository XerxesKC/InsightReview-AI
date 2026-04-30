package com.example.mybatisplusdemo.service.impl;

import com.example.mybatisplusdemo.model.domain.CommentImages;
import com.example.mybatisplusdemo.mapper.CommentImagesMapper;
import com.example.mybatisplusdemo.service.ICommentImagesService;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import org.springframework.stereotype.Service;


@Service
public class CommentImagesServiceImpl extends ServiceImpl<CommentImagesMapper, CommentImages> implements ICommentImagesService {

}
