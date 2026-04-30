package com.example.mybatisplusdemo.service.impl;

import com.example.mybatisplusdemo.model.domain.CommentVideos;
import com.example.mybatisplusdemo.mapper.CommentVideosMapper;
import com.example.mybatisplusdemo.service.ICommentVideosService;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import org.springframework.stereotype.Service;


@Service
public class CommentVideosServiceImpl extends ServiceImpl<CommentVideosMapper, CommentVideos> implements ICommentVideosService {

}
