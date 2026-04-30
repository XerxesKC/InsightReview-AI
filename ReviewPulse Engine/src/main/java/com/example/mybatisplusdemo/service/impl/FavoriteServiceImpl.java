package com.example.mybatisplusdemo.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.mybatisplusdemo.model.domain.Favorite;
import com.example.mybatisplusdemo.mapper.FavoriteMapper;
import com.example.mybatisplusdemo.model.domain.User;
import com.example.mybatisplusdemo.model.dto.FavoriteDTO;
import com.example.mybatisplusdemo.model.dto.FavoriteInsertDTO;
import com.example.mybatisplusdemo.model.dto.FavoriteUpdateDTO;
import com.example.mybatisplusdemo.service.IFavoriteService;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import org.springframework.stereotype.Service;
import com.example.mybatisplusdemo.model.vo.FavoriteSearchVO;
import com.example.mybatisplusdemo.model.dto.FavoriteSearchDTO;

import java.time.LocalDateTime;


@Service
public class FavoriteServiceImpl extends ServiceImpl<FavoriteMapper, Favorite> implements IFavoriteService {

    @Override
    public Page<Favorite> searchFavorite(Page<Favorite> page, FavoriteDTO favoriteDTO) {
        QueryWrapper<Favorite> query = new QueryWrapper<>();
        if (favoriteDTO.getUserId() != null && !favoriteDTO.getUserId().isEmpty()) {
            query.eq("user_id", favoriteDTO.getUserId());
        }
        if (favoriteDTO.getMerchantId() != null && !favoriteDTO.getMerchantId().isEmpty()) {
            query.eq("merchant_id", favoriteDTO.getMerchantId());
        }
        if (favoriteDTO.getTag() != null && !favoriteDTO.getTag().isEmpty()) {
            query.like("tag", favoriteDTO.getTag());
        }
        query.eq("is_deleted", "0");
        return this.page(page, query);
    }

    @Override
    public Page<FavoriteSearchVO> searchFavorite(Page<FavoriteSearchVO> page, FavoriteSearchDTO favoriteSearchDTO) {
        return baseMapper.searchFavoriteVO(page, favoriteSearchDTO);
    }

    @Override
    public Favorite insertFavorite(FavoriteInsertDTO favoriteInsertDTO) {
        Favorite favorite = new Favorite();
        favorite.setUserId(favoriteInsertDTO.getUserId());
        favorite.setMerchantId(favoriteInsertDTO.getMerchantId());
        favorite.setTag(favoriteInsertDTO.getTag());
        favorite.setCreateTime(LocalDateTime.now());
        favorite.setUpdateTime(LocalDateTime.now());
        favorite.setIsDeleted("F");
        this.save(favorite);
        return favorite;
    }

    @Override
    public Favorite updateFavorite(FavoriteUpdateDTO favoriteUpdateDTO) {
        Favorite favorite = this.getById(favoriteUpdateDTO.getFavoriteId());
        if (favorite == null) return null;
        if (favoriteUpdateDTO.getTag() != null && !favoriteUpdateDTO.getTag().isEmpty()) {
            favorite.setTag(favoriteUpdateDTO.getTag());
        }
        if (favoriteUpdateDTO.getMerchantId() != null && !favoriteUpdateDTO.getMerchantId().isEmpty()) {
            favorite.setMerchantId(favoriteUpdateDTO.getMerchantId());
        }
        if (favoriteUpdateDTO.getUserId() != null && !favoriteUpdateDTO.getUserId().isEmpty()) {
            favorite.setUserId(favoriteUpdateDTO.getUserId());
        }
        favorite.setUpdateTime(LocalDateTime.now());
        boolean result = this.updateById(favorite);
        return result ? favorite : null;
    }

    @Override
    public Favorite deleteFavorite(String favoriteId) {
        Favorite favorite = getById(favoriteId);
        if (favorite == null) {
            return null;
        }
        favorite.setIsDeleted("T");
        favorite.setUpdateTime(java.time.LocalDateTime.now());
        updateById(favorite);
        return favorite;
    }
}
