package com.example.mybatisplusdemo.service;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.mybatisplusdemo.model.domain.Merchantpost;
import com.baomidou.mybatisplus.extension.service.IService;

import java.util.List;


public interface IMerchantpostService extends IService<Merchantpost> {

    List<Merchantpost> getContents(String merchantId);

    boolean deleteContent(String postId);

    Integer addLikeCount(Merchantpost merchantpost);
}
