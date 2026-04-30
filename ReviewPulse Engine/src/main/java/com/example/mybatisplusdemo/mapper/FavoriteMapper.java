package com.example.mybatisplusdemo.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.mybatisplusdemo.model.domain.Favorite;
import com.example.mybatisplusdemo.model.dto.FavoriteSearchDTO;
import com.example.mybatisplusdemo.model.vo.FavoriteSearchVO;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;


public interface FavoriteMapper extends BaseMapper<Favorite> {
    Page<FavoriteSearchVO> searchFavoriteVO(Page<FavoriteSearchVO> page, FavoriteSearchDTO favoriteSearchDTO);
}
