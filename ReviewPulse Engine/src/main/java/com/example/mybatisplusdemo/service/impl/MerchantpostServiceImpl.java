package com.example.mybatisplusdemo.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.mybatisplusdemo.common.JsonResponse;
import com.example.mybatisplusdemo.common.utls.SessionUtils;
import com.example.mybatisplusdemo.mapper.MerchantMapper;
import com.example.mybatisplusdemo.model.domain.Comment;
import com.example.mybatisplusdemo.model.domain.Merchant;
import com.example.mybatisplusdemo.model.domain.Merchantpost;
import com.example.mybatisplusdemo.mapper.MerchantpostMapper;
import com.example.mybatisplusdemo.model.domain.User;
import com.example.mybatisplusdemo.service.IMerchantpostService;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;


@Service
public class MerchantpostServiceImpl extends ServiceImpl<MerchantpostMapper, Merchantpost> implements IMerchantpostService {

    private final MerchantpostMapper merchantpostMapper;

    public MerchantpostServiceImpl(MerchantpostMapper merchantpostMapper) {
        this.merchantpostMapper = merchantpostMapper;
    }

    @Override
    public List<Merchantpost> getContents(String merchantId) {
        List<Merchantpost> list = new ArrayList<>();
        list = merchantpostMapper.getContents(merchantId);
        return list;
    }

    @Override
    public boolean deleteContent(String postId) {
        return merchantpostMapper.deleteContent(postId);
    }

    @Override
    public Integer addLikeCount(Merchantpost merchantpost) {
        return merchantpostMapper.addLikeCount(merchantpost);
    }
}
